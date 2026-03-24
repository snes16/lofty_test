import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3

from models import (
    EthBalance,
    LiquidityResponse,
    PortfolioResponse,
    TokensResponse,
)
from services.cache import cache
from services.eth import get_eth_balance
from services.tokens import get_token_balances
from services.uniswap_v2 import get_v2_positions
from services.uniswap_v3 import get_v3_positions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Web3 Portfolio Dashboard API",
    description="Real-time portfolio tracker for Ethereum wallets",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_address(address: str) -> str:
    """Validate and return checksum address, raise 400 if invalid."""
    if not Web3.is_address(address):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Ethereum address: {address}",
        )
    return Web3.to_checksum_address(address)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/balance/eth/{address}", response_model=EthBalance)
async def get_eth_balance_endpoint(address: str):
    """
    Get ETH balance and USD value for an Ethereum address.
    """
    checksum_address = validate_address(address)
    try:
        return await get_eth_balance(checksum_address)
    except Exception as exc:
        logger.error("Error fetching ETH balance for %s: %s", address, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/balance/tokens/{address}", response_model=TokensResponse)
async def get_tokens_endpoint(address: str):
    """
    Get all ERC-20 token balances and USD values for an Ethereum address.
    """
    checksum_address = validate_address(address)
    try:
        return await get_token_balances(checksum_address)
    except Exception as exc:
        logger.error("Error fetching token balances for %s: %s", address, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/liquidity/{address}", response_model=LiquidityResponse)
async def get_liquidity_endpoint(address: str):
    """
    Get all Uniswap V2 and V3 liquidity positions for an Ethereum address.
    """
    checksum_address = validate_address(address)
    cache_key = f"liquidity:{checksum_address.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        v2_positions, v3_positions = await asyncio.gather(
            get_v2_positions(checksum_address),
            get_v3_positions(checksum_address),
        )

        v2_total = sum(p.total_usd for p in v2_positions)
        v3_total = sum(p.total_usd for p in v3_positions)
        total_usd = v2_total + v3_total

        result = LiquidityResponse(
            address=checksum_address,
            v2_positions=v2_positions,
            v3_positions=v3_positions,
            total_usd=total_usd,
        )
        cache.set(cache_key, result)
        return result
    except Exception as exc:
        logger.error("Error fetching liquidity for %s: %s", address, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/portfolio/{address}", response_model=PortfolioResponse)
async def get_portfolio_endpoint(address: str):
    """
    Get complete portfolio overview including ETH balance, tokens, and LP positions.
    All data fetched in parallel for performance.
    """
    checksum_address = validate_address(address)
    cache_key = f"portfolio:{checksum_address.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        eth_data, tokens_data, v2_positions, v3_positions = await asyncio.gather(
            get_eth_balance(checksum_address),
            get_token_balances(checksum_address),
            get_v2_positions(checksum_address),
            get_v3_positions(checksum_address),
        )

        v2_total = sum(p.total_usd for p in v2_positions)
        v3_total = sum(p.total_usd for p in v3_positions)
        liquidity_total = v2_total + v3_total

        liquidity = LiquidityResponse(
            address=checksum_address,
            v2_positions=v2_positions,
            v3_positions=v3_positions,
            total_usd=liquidity_total,
        )

        total_usd = eth_data.balance_usd + tokens_data.total_usd + liquidity_total

        result = PortfolioResponse(
            address=checksum_address,
            eth=eth_data,
            tokens=tokens_data,
            liquidity=liquidity,
            total_usd=total_usd,
            last_updated=datetime.now(timezone.utc),
        )
        cache.set(cache_key, result)
        return result
    except Exception as exc:
        logger.error("Error fetching portfolio for %s: %s", address, exc)
        raise HTTPException(status_code=500, detail=str(exc))
