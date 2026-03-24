import json
import logging
from pathlib import Path

import httpx
from web3 import Web3

from models import UniswapV2Position
from services.cache import cache
from services.prices import get_token_prices

logger = logging.getLogger(__name__)

ABI_DIR = Path(__file__).parent.parent / "abi"

with open(ABI_DIR / "univ2_pair.json") as f:
    UNIV2_PAIR_ABI = json.load(f)

with open(ABI_DIR / "erc20.json") as f:
    ERC20_ABI = json.load(f)

UNISWAP_V2_SUBGRAPH = (
    "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
)

UNISWAP_V2_GRAPH_QUERY = """
query LiquidityPositions($user: String!) {
  liquidityPositions(where: { user: $user, liquidityTokenBalance_gt: "0" }) {
    id
    liquidityTokenBalance
    pair {
      id
      token0 {
        id
        symbol
        decimals
      }
      token1 {
        id
        symbol
        decimals
      }
      reserve0
      reserve1
      totalSupply
    }
  }
}
"""


def _calculate_v2_position(
    lp_balance: float,
    total_supply: float,
    reserve0: float,
    reserve1: float,
    decimals0: int,
    decimals1: int,
    price0_usd: float,
    price1_usd: float,
    pair_address: str,
    token0_symbol: str,
    token1_symbol: str,
) -> UniswapV2Position:
    """Calculate UniswapV2 position amounts and USD value from reserves."""
    if total_supply <= 0:
        share_percent = 0.0
        token0_amount = 0.0
        token1_amount = 0.0
    else:
        user_share = lp_balance / total_supply
        share_percent = user_share * 100.0
        token0_amount = user_share * reserve0 / (10 ** decimals0)
        token1_amount = user_share * reserve1 / (10 ** decimals1)

    total_usd = token0_amount * price0_usd + token1_amount * price1_usd

    return UniswapV2Position(
        pair_address=pair_address,
        token0_symbol=token0_symbol,
        token1_symbol=token1_symbol,
        token0_amount=token0_amount,
        token1_amount=token1_amount,
        total_usd=total_usd,
        lp_balance=lp_balance,
        share_percent=share_percent,
    )


async def _fetch_from_subgraph(address: str) -> list[dict]:
    """Query The Graph for Uniswap V2 liquidity positions."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            UNISWAP_V2_SUBGRAPH,
            json={
                "query": UNISWAP_V2_GRAPH_QUERY,
                "variables": {"user": address.lower()},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise ValueError(f"GraphQL errors: {data['errors']}")
        return data.get("data", {}).get("liquidityPositions", [])


async def get_v2_positions(address: str) -> list[UniswapV2Position]:
    """
    Fetch Uniswap V2 liquidity positions for the given address.
    Falls back to empty list with a warning if The Graph is unavailable.
    """
    checksum_address = Web3.to_checksum_address(address)
    cache_key = f"v2_positions:{checksum_address.lower()}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    positions: list[UniswapV2Position] = []

    try:
        raw_positions = await _fetch_from_subgraph(checksum_address)
    except Exception as exc:
        logger.warning(
            "Uniswap V2 subgraph unavailable for %s: %s. Returning empty list.",
            address,
            exc,
        )
        cache.set(cache_key, positions)
        return positions

    if not raw_positions:
        cache.set(cache_key, positions)
        return positions

    # Gather token addresses for price lookup
    token_addresses: list[str] = []
    for pos in raw_positions:
        pair = pos.get("pair", {})
        token_addresses.append(pair.get("token0", {}).get("id", "").lower())
        token_addresses.append(pair.get("token1", {}).get("id", "").lower())

    token_addresses = list(set(a for a in token_addresses if a))
    prices = await get_token_prices(token_addresses)

    for pos in raw_positions:
        try:
            pair = pos["pair"]
            lp_balance = float(pos["liquidityTokenBalance"])

            token0 = pair["token0"]
            token1 = pair["token1"]
            token0_id = token0["id"].lower()
            token1_id = token1["id"].lower()

            total_supply = float(pair["totalSupply"])
            reserve0 = float(pair["reserve0"])
            reserve1 = float(pair["reserve1"])
            decimals0 = int(token0.get("decimals", 18))
            decimals1 = int(token1.get("decimals", 18))

            price0 = prices.get(token0_id, 0.0)
            price1 = prices.get(token1_id, 0.0)

            position = _calculate_v2_position(
                lp_balance=lp_balance,
                total_supply=total_supply,
                reserve0=reserve0,
                reserve1=reserve1,
                decimals0=decimals0,
                decimals1=decimals1,
                price0_usd=price0,
                price1_usd=price1,
                pair_address=Web3.to_checksum_address(pair["id"]),
                token0_symbol=token0.get("symbol", "TOKEN0"),
                token1_symbol=token1.get("symbol", "TOKEN1"),
            )
            positions.append(position)

        except Exception as exc:
            logger.warning("Failed to process V2 position %s: %s", pos, exc)
            continue

    cache.set(cache_key, positions)
    return positions
