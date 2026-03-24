import { useState, useCallback } from 'react'
import type { PortfolioResponse, LoadingState } from './types'
import { getPortfolio, ApiError } from './api/portfolio'

import AddressInput from './components/AddressInput'
import PortfolioSummary from './components/PortfolioSummary'
import EthCard from './components/EthCard'
import TokensTable from './components/TokensTable'
import LiquidityPositions from './components/LiquidityPositions'
import ErrorBanner from './components/ErrorBanner'

// Empty portfolio placeholder for skeleton loading state
const EMPTY_PORTFOLIO: PortfolioResponse = {
  address: '',
  eth: { address: '', balance_eth: 0, balance_usd: 0 },
  tokens: { address: '', tokens: [], total_usd: 0 },
  liquidity: {
    address: '',
    v2_positions: [],
    v3_positions: [],
    total_usd: 0,
  },
  total_usd: 0,
  last_updated: new Date().toISOString(),
}

export default function App() {
  const [loadingState, setLoadingState] = useState<LoadingState>('idle')
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const handleAnalyze = useCallback(async (address: string) => {
    setLoadingState('loading')
    setError(null)

    try {
      const data = await getPortfolio(address)
      setPortfolio(data)
      setLoadingState('success')
    } catch (err) {
      let message = 'An unexpected error occurred. Please try again.'

      if (err instanceof ApiError) {
        if (err.status === 400) {
          message = `Invalid address: ${err.detail}`
        } else if (err.status === 429) {
          message = 'Rate limited. Please wait a moment and try again.'
        } else if (err.status >= 500) {
          message = `Server error: ${err.detail}`
        } else {
          message = err.detail
        }
      } else if (err instanceof TypeError && err.message.includes('fetch')) {
        message = 'Cannot connect to the API. Make sure the backend is running on http://localhost:8000.'
      }

      setError(message)
      setLoadingState('error')
    }
  }, [])

  const isLoading = loadingState === 'loading'
  const showData = loadingState === 'success' || loadingState === 'loading'
  const displayPortfolio = portfolio ?? EMPTY_PORTFOLIO

  return (
    <div
      className="min-h-screen bg-grid-pattern"
      style={{ background: '#0a0a0f' }}
    >
      {/* Ambient glow elements */}
      <div
        className="fixed top-0 left-1/4 w-96 h-96 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      <div
        className="fixed bottom-0 right-1/4 w-96 h-96 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(168,85,247,0.06) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />

      {/* Main layout */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Navbar / Brand */}
        <header className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #6366f1, #4f52d4)',
                boxShadow: '0 0 20px rgba(99,102,241,0.4)',
              }}
            >
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L6 12l6 4 6-4-6-10zM6 13.5l6 3.5 6-3.5L12 21 6 13.5z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-100 leading-tight">
                Web3 Portfolio
              </h1>
              <p className="text-xs text-slate-600">Ethereum Dashboard</p>
            </div>
          </div>

          {/* Chain indicator */}
          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
            style={{
              background: 'rgba(34,197,94,0.1)',
              border: '1px solid rgba(34,197,94,0.2)',
              color: '#22c55e',
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block animate-pulse" />
            Ethereum Mainnet
          </div>
        </header>

        {/* Address Input */}
        <AddressInput onAnalyze={handleAnalyze} isLoading={isLoading} />

        {/* Error Banner */}
        {error && (
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        )}

        {/* Portfolio Data */}
        {showData && (
          <div className="space-y-6 animate-fade-in">
            {/* Summary */}
            <PortfolioSummary
              portfolio={displayPortfolio}
              isLoading={isLoading}
            />

            {/* ETH + Tokens row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* ETH Card */}
              <div className="md:col-span-1">
                <EthCard eth={displayPortfolio.eth} isLoading={isLoading} />
              </div>

              {/* Tokens Table */}
              <div className="md:col-span-2">
                <TokensTable
                  tokens={displayPortfolio.tokens}
                  isLoading={isLoading}
                />
              </div>
            </div>

            {/* Liquidity Positions */}
            <LiquidityPositions
              liquidity={displayPortfolio.liquidity}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* Idle / Initial state CTA */}
        {loadingState === 'idle' && (
          <div className="text-center py-16 animate-fade-in">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{
                background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(99,102,241,0.05))',
                border: '1px solid rgba(99,102,241,0.2)',
              }}
            >
              <svg
                className="w-8 h-8 text-indigo-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-slate-300 mb-2">
              Analyze Any Ethereum Wallet
            </h2>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Enter an Ethereum address above to see its complete portfolio including
              ETH balance, ERC-20 tokens, and Uniswap V2/V3 liquidity positions.
            </p>

            {/* Feature cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-xl mx-auto mt-8">
              {[
                { icon: '⟠', title: 'ETH Balance', desc: 'Real-time ETH with USD value' },
                { icon: '◈', title: 'Token Holdings', desc: 'All ERC-20 tokens with prices' },
                { icon: '⇄', title: 'LP Positions', desc: 'Uniswap V2 & V3 positions' },
              ].map((feature) => (
                <div
                  key={feature.title}
                  className="glass-card-inner p-4 text-center"
                >
                  <div className="text-2xl mb-2">{feature.icon}</div>
                  <p className="text-sm font-medium text-slate-300">{feature.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="text-center pt-6 pb-2">
          <p className="text-xs text-slate-700">
            Data from Alchemy &bull; CoinGecko &bull; The Graph &bull; Uniswap V3
          </p>
        </footer>
      </div>
    </div>
  )
}
