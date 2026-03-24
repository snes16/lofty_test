// ============================================================
// TypeScript types matching backend Pydantic models
// ============================================================

export interface EthBalance {
  address: string
  balance_eth: number
  balance_usd: number
}

export interface TokenBalance {
  contract_address: string
  symbol: string
  name: string
  balance: number
  price_usd: number
  balance_usd: number
  logo_url: string | null
}

export interface TokensResponse {
  address: string
  tokens: TokenBalance[]
  total_usd: number
}

export interface UniswapV2Position {
  pair_address: string
  token0_symbol: string
  token1_symbol: string
  token0_amount: number
  token1_amount: number
  total_usd: number
  lp_balance: number
  share_percent: number
}

export interface UniswapV3Position {
  token_id: number
  token0_symbol: string
  token1_symbol: string
  fee_tier: number
  token0_amount: number
  token1_amount: number
  fees0_earned: number
  fees1_earned: number
  total_usd: number
  in_range: boolean
  tick_lower: number
  tick_upper: number
  current_tick: number
}

export interface LiquidityResponse {
  address: string
  v2_positions: UniswapV2Position[]
  v3_positions: UniswapV3Position[]
  total_usd: number
}

export interface PortfolioResponse {
  address: string
  eth: EthBalance
  tokens: TokensResponse
  liquidity: LiquidityResponse
  total_usd: number
  last_updated: string
}

// API error shape
export interface ApiError {
  detail: string
}

// Loading state
export type LoadingState = 'idle' | 'loading' | 'success' | 'error'
