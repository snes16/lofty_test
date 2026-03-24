import logging

from web3 import Web3

from config import settings
from models import EthBalance
from services.cache import cache
from services.prices import get_eth_price

logger = logging.getLogger(__name__)

_w3: Web3 | None = None


def get_web3() -> Web3:
    global _w3
    if _w3 is None or not _w3.is_connected():
        _w3 = Web3(Web3.HTTPProvider(settings.eth_rpc_url))
    return _w3


async def get_eth_balance(address: str) -> EthBalance:
    """
    Fetch ETH balance for the given address and return an EthBalance model
    with USD valuation.
    """
    checksum_address = Web3.to_checksum_address(address)
    cache_key = f"eth_balance:{checksum_address.lower()}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    w3 = get_web3()

    try:
        wei_balance = w3.eth.get_balance(checksum_address)
        balance_eth = float(Web3.from_wei(wei_balance, "ether"))
    except Exception as exc:
        logger.error("Failed to fetch ETH balance for %s: %s", address, exc)
        balance_eth = 0.0

    eth_price = await get_eth_price()
    balance_usd = balance_eth * eth_price

    result = EthBalance(
        address=checksum_address,
        balance_eth=balance_eth,
        balance_usd=balance_usd,
    )

    cache.set(cache_key, result)
    return result
