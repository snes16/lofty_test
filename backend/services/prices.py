import asyncio
import logging
from typing import Optional

import httpx

from services.cache import cache

logger = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BATCH_SIZE = 50  # CoinGecko allows up to ~50 addresses per request


async def get_eth_price() -> float:
    """Fetch current ETH price in USD from CoinGecko."""
    cache_key = "eth_price"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={"ids": "ethereum", "vs_currencies": "usd"},
            )
            resp.raise_for_status()
            data = resp.json()
            price = float(data["ethereum"]["usd"])
            cache.set(cache_key, price)
            return price
    except Exception as exc:
        logger.warning("Failed to fetch ETH price from CoinGecko: %s", exc)
        # Return cached stale value if available, else 0
        cached_stale = cache.get(cache_key)
        return cached_stale if cached_stale is not None else 0.0


async def get_token_prices(contract_addresses: list[str]) -> dict[str, float]:
    """
    Fetch token prices in USD from CoinGecko for a list of Ethereum contract addresses.
    Returns a dict mapping lowercase contract address -> USD price.
    """
    if not contract_addresses:
        return {}

    addresses_lower = [a.lower() for a in contract_addresses]
    cache_key = "token_prices:" + ",".join(sorted(addresses_lower))
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    prices: dict[str, float] = {}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Process in batches
            for i in range(0, len(addresses_lower), BATCH_SIZE):
                batch = addresses_lower[i : i + BATCH_SIZE]
                contract_list = ",".join(batch)

                try:
                    resp = await client.get(
                        f"{COINGECKO_BASE}/simple/token_price/ethereum",
                        params={
                            "contract_addresses": contract_list,
                            "vs_currencies": "usd",
                            "include_market_cap": "false",
                            "include_24hr_vol": "false",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for addr, price_data in data.items():
                        if "usd" in price_data:
                            prices[addr.lower()] = float(price_data["usd"])

                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        "CoinGecko token price batch %d failed: %s", i // BATCH_SIZE, exc
                    )

                # Respect rate limits between batches
                if i + BATCH_SIZE < len(addresses_lower):
                    await asyncio.sleep(0.5)

    except Exception as exc:
        logger.warning("Failed to fetch token prices from CoinGecko: %s", exc)

    cache.set(cache_key, prices)
    return prices


async def get_token_price_by_id(coingecko_id: str) -> Optional[float]:
    """Fetch price for a specific CoinGecko coin ID."""
    cache_key = f"coin_price:{coingecko_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={"ids": coingecko_id, "vs_currencies": "usd"},
            )
            resp.raise_for_status()
            data = resp.json()
            if coingecko_id in data and "usd" in data[coingecko_id]:
                price = float(data[coingecko_id]["usd"])
                cache.set(cache_key, price)
                return price
    except Exception as exc:
        logger.warning("Failed to fetch price for %s: %s", coingecko_id, exc)

    return None
