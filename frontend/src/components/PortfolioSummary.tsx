import type { PortfolioResponse } from '../types'

interface PortfolioSummaryProps {
  portfolio: PortfolioResponse
  isLoading?: boolean
}

function formatUSD(value: number): string {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(2)}K`
  }
  return `$${value.toFixed(2)}`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

interface StatTileProps {
  label: string
  value: string
  percent?: number
  color: string
  icon: React.ReactNode
}

function StatTile({ label, value, percent, color, icon }: StatTileProps) {
  return (
    <div className="stat-tile">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: `${color}20`, color }}>
          {icon}
        </div>
      </div>
      <p className="num text-lg font-bold text-slate-200">{value}</p>
      {percent !== undefined && (
        <p className="text-xs text-slate-500 mt-0.5">
          {percent.toFixed(1)}% of portfolio
        </p>
      )}
    </div>
  )
}

export default function PortfolioSummary({ portfolio, isLoading }: PortfolioSummaryProps) {
  const { total_usd, eth, tokens, liquidity, last_updated } = portfolio

  const ethPercent = total_usd > 0 ? (eth.balance_usd / total_usd) * 100 : 0
  const tokensPercent = total_usd > 0 ? (tokens.total_usd / total_usd) * 100 : 0
  const lpPercent = total_usd > 0 ? (liquidity.total_usd / total_usd) * 100 : 0

  return (
    <div className="glass-card p-6 md:p-8 animate-slide-up">
      {/* Total Portfolio Value */}
      <div className="text-center mb-8">
        <p className="text-sm font-medium text-slate-500 uppercase tracking-widest mb-2">
          Total Portfolio Value
        </p>
        <div className="relative inline-block">
          <h1
            className="num font-extrabold text-transparent bg-clip-text"
            style={{
              fontSize: 'clamp(2.5rem, 6vw, 4rem)',
              lineHeight: 1.1,
              backgroundImage: 'linear-gradient(135deg, #e2e8f0 0%, #818cf8 50%, #6366f1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            {isLoading ? (
              <span className="skeleton inline-block w-48 h-14 rounded-lg" />
            ) : (
              formatUSD(total_usd)
            )}
          </h1>
        </div>

        {last_updated && (
          <p className="text-xs text-slate-600 mt-3">
            Last updated: {formatDate(last_updated)}
          </p>
        )}
      </div>

      {/* Breakdown Bar */}
      {total_usd > 0 && !isLoading && (
        <div className="mb-6">
          <div className="flex rounded-full overflow-hidden h-2 gap-px">
            {ethPercent > 0 && (
              <div
                className="transition-all duration-500"
                style={{ width: `${ethPercent}%`, background: '#6366f1' }}
                title={`ETH: ${ethPercent.toFixed(1)}%`}
              />
            )}
            {tokensPercent > 0 && (
              <div
                className="transition-all duration-500"
                style={{ width: `${tokensPercent}%`, background: '#22c55e' }}
                title={`Tokens: ${tokensPercent.toFixed(1)}%`}
              />
            )}
            {lpPercent > 0 && (
              <div
                className="transition-all duration-500"
                style={{ width: `${lpPercent}%`, background: '#f59e0b' }}
                title={`LP: ${lpPercent.toFixed(1)}%`}
              />
            )}
          </div>
          <div className="flex justify-between text-xs text-slate-600 mt-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-500 inline-block" />
              ETH
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
              Tokens
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
              Liquidity
            </span>
          </div>
        </div>
      )}

      {/* Stat Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <StatTile
          label="ETH"
          value={isLoading ? '—' : formatUSD(eth.balance_usd)}
          percent={isLoading ? undefined : ethPercent}
          color="#6366f1"
          icon={
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L6 12l6 4 6-4-6-10zM6 13.5l6 3.5 6-3.5L12 21 6 13.5z" />
            </svg>
          }
        />
        <StatTile
          label="Tokens"
          value={isLoading ? '—' : formatUSD(tokens.total_usd)}
          percent={isLoading ? undefined : tokensPercent}
          color="#22c55e"
          icon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
            </svg>
          }
        />
        <StatTile
          label="Liquidity"
          value={isLoading ? '—' : formatUSD(liquidity.total_usd)}
          percent={isLoading ? undefined : lpPercent}
          color="#f59e0b"
          icon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
            </svg>
          }
        />
      </div>
    </div>
  )
}
