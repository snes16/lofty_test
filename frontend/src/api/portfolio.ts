import type {
  EthBalance,
  TokensResponse,
  LiquidityResponse,
  PortfolioResponse,
} from '../types'

// Empty string = relative URLs (works on Vercel where frontend + backend share a domain).
// Override with VITE_API_URL env var for local dev pointing at a separate backend.
const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? ''

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

async function fetchJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // ignore parse error
    }
    throw new ApiError(response.status, detail)
  }

  return response.json() as Promise<T>
}

/**
 * Fetch ETH balance and USD value for the given address.
 */
export async function getEthBalance(address: string): Promise<EthBalance> {
  return fetchJSON<EthBalance>(`/balance/eth/${encodeURIComponent(address)}`)
}

/**
 * Fetch all ERC-20 token balances for the given address.
 */
export async function getTokenBalances(address: string): Promise<TokensResponse> {
  return fetchJSON<TokensResponse>(`/balance/tokens/${encodeURIComponent(address)}`)
}

/**
 * Fetch all Uniswap V2 and V3 liquidity positions for the given address.
 */
export async function getLiquidityPositions(address: string): Promise<LiquidityResponse> {
  return fetchJSON<LiquidityResponse>(`/liquidity/${encodeURIComponent(address)}`)
}

/**
 * Fetch the full portfolio overview for the given address.
 * This is the primary endpoint — it fetches all data in one call.
 */
export async function getPortfolio(address: string): Promise<PortfolioResponse> {
  return fetchJSON<PortfolioResponse>(`/portfolio/${encodeURIComponent(address)}`)
}

/**
 * Health check.
 */
export async function checkHealth(): Promise<{ status: string }> {
  return fetchJSON<{ status: string }>('/health')
}

export { ApiError }
