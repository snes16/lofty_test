from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class EthBalance(BaseModel):
    address: str
    balance_eth: float
    balance_usd: float


class TokenBalance(BaseModel):
    contract_address: str
    symbol: str
    name: str
    balance: float
    price_usd: float
    balance_usd: float
    logo_url: Optional[str] = None


class TokensResponse(BaseModel):
    address: str
    tokens: list[TokenBalance]
    total_usd: float


class UniswapV2Position(BaseModel):
    pair_address: str
    token0_symbol: str
    token1_symbol: str
    token0_amount: float
    token1_amount: float
    total_usd: float
    lp_balance: float
    share_percent: float


class UniswapV2Response(BaseModel):
    address: str
    positions: list[UniswapV2Position]
    total_usd: float


class UniswapV3Position(BaseModel):
    token_id: int
    token0_symbol: str
    token1_symbol: str
    fee_tier: int
    token0_amount: float
    token1_amount: float
    fees0_earned: float
    fees1_earned: float
    total_usd: float
    in_range: bool
    tick_lower: int
    tick_upper: int
    current_tick: int


class UniswapV3Response(BaseModel):
    address: str
    positions: list[UniswapV3Position]
    total_usd: float


class LiquidityResponse(BaseModel):
    address: str
    v2_positions: list[UniswapV2Position]
    v3_positions: list[UniswapV3Position]
    total_usd: float


class PortfolioResponse(BaseModel):
    address: str
    eth: EthBalance
    tokens: TokensResponse
    liquidity: LiquidityResponse
    total_usd: float
    last_updated: datetime
