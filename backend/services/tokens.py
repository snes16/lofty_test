import json
import logging
from pathlib import Path

import httpx
from web3 import Web3

from config import settings
from models import TokenBalance, TokensResponse
from services.cache import cache
from services.prices import get_token_prices

logger = logging.getLogger(__name__)

ABI_DIR = Path(__file__).parent.parent / "abi"

with open(ABI_DIR / "erc20.json") as f:
    ERC20_ABI = json.load(f)

DUST_THRESHOLD_USD = 0.01


async def _alchemy_get_token_balances(address: str) -> list[dict]:
    """Use Alchemy's alchemy_getTokenBalances RPC method."""
    url = settings.eth_rpc_url
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getTokenBalances",
        "params": [address, "erc20"],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(f"Alchemy error: {data['error']}")
        return data.get("result", {}).get("tokenBalances", [])


async def _alchemy_get_token_metadata(contract_address: str) -> dict:
    """Use Alchemy's alchemy_getTokenMetadata RPC method."""
    url = settings.eth_rpc_url
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getTokenMetadata",
        "params": [contract_address],
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(f"Alchemy metadata error: {data['error']}")
        return data.get("result", {})


def _hex_to_int(hex_str: str) -> int:
    """Convert hex string (0x...) to integer."""
    if not hex_str or hex_str == "0x":
        return 0
    return int(hex_str, 16)


async def get_token_balances(address: str) -> TokensResponse:
    """
    Fetch ERC-20 token balances for the given address.
    Uses Alchemy's enhanced APIs for metadata retrieval.
    Filters out dust positions (balance_usd < DUST_THRESHOLD_USD).
    """
    checksum_address = Web3.to_checksum_address(address)
    cache_key = f"token_balances:{checksum_address.lower()}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        raw_balances = await _alchemy_get_token_balances(checksum_address)
    except Exception as exc:
        logger.error("Failed to fetch token balances for %s: %s", address, exc)
        result = TokensResponse(address=checksum_address, tokens=[], total_usd=0.0)
        return result

    # Filter out zero balances
    non_zero = [
        b for b in raw_balances
        if b.get("tokenBalance") and _hex_to_int(b["tokenBalance"]) > 0
    ]

    if not non_zero:
        result = TokensResponse(address=checksum_address, tokens=[], total_usd=0.0)
        cache.set(cache_key, result)
        return result

    # Collect contract addresses for price lookup
    contract_addresses = [b["contractAddress"].lower() for b in non_zero]
    prices = await get_token_prices(contract_addresses)

    tokens: list[TokenBalance] = []

    for token_data in non_zero:
        contract_addr = token_data["contractAddress"]
        raw_balance = _hex_to_int(token_data["tokenBalance"])

        try:
            metadata = await _alchemy_get_token_metadata(contract_addr)
            decimals = int(metadata.get("decimals") or 18)
            symbol = metadata.get("symbol") or "UNKNOWN"
            name = metadata.get("name") or "Unknown Token"
            logo_url = metadata.get("logo")
        except Exception as exc:
            logger.warning("Failed metadata for %s: %s", contract_addr, exc)
            decimals = 18
            symbol = "UNKNOWN"
            name = "Unknown Token"
            logo_url = None

        if decimals == 0:
            decimals = 18

        balance = raw_balance / (10 ** decimals)
        price_usd = prices.get(contract_addr.lower(), 0.0)
        balance_usd = balance * price_usd

        # Filter dust
        if balance_usd < DUST_THRESHOLD_USD and price_usd > 0:
            continue

        tokens.append(
            TokenBalance(
                contract_address=Web3.to_checksum_address(contract_addr),
                symbol=symbol,
                name=name,
                balance=balance,
                price_usd=price_usd,
                balance_usd=balance_usd,
                logo_url=logo_url if logo_url else None,
            )
        )

    # Sort by USD value descending
    tokens.sort(key=lambda t: t.balance_usd, reverse=True)
    total_usd = sum(t.balance_usd for t in tokens)

    result = TokensResponse(
        address=checksum_address,
        tokens=tokens,
        total_usd=total_usd,
    )
    cache.set(cache_key, result)
    return result
