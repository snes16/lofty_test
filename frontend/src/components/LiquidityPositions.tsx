import type { LiquidityResponse, UniswapV2Position, UniswapV3Position } from '../types'

interface LiquidityPositionsProps {
  liquidity: LiquidityResponse
  isLoading?: boolean
}

function formatAmount(amount: number): string {
  if (amount === 0) return '0'
  if (amount < 0.000001) return amount.toExponential(2)
  if (amount < 0.01) return amount.toFixed(6)
  if (amount < 1000) return amount.toFixed(4)
  return amount.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function formatUSD(value: number): string {
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatFeeTier(fee: number): string {
  return `${(fee / 10000).toFixed(2)}%`
}

function shortenAddress(addr: string): string {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`
}

// ---------------------------------------------------------------
// V2 Position Card
// ---------------------------------------------------------------
function V2PositionCard({ position }: { position: UniswapV2Position }) {
  return (
    <div className="glass-card-inner p-4 space-y-3">
      {/* Pair header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="px-2.5 py-1 rounded-lg text-xs font-bold"
            style={{
              background: 'rgba(99,102,241,0.15)',
              color: '#818cf8',
              border: '1px solid rgba(99,102,241,0.2)',
            }}
          >
            V2
          </div>
          <span className="font-semibold text-slate-200">
            {position.token0_symbol}/{position.token1_symbol}
          </span>
        </div>
        <span className="num font-bold text-slate-200">{formatUSD(position.total_usd)}</span>
      </div>

      {/* Token amounts */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-2.5 rounded-lg" style={{ background: 'rgba(10,10,15,0.5)' }}>
          <p className="text-xs text-slate-500 mb-1">{position.token0_symbol}</p>
          <p className="num text-sm font-semibold text-slate-200">
            {formatAmount(position.token0_amount)}
          </p>
        </div>
        <div className="p-2.5 rounded-lg" style={{ background: 'rgba(10,10,15,0.5)' }}>
          <p className="text-xs text-slate-500 mb-1">{position.token1_symbol}</p>
          <p className="num text-sm font-semibold text-slate-200">
            {formatAmount(position.token1_amount)}
          </p>
        </div>
      </div>

      {/* Share + pair address */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Pool share: <span className="num text-slate-400">{position.share_percent.toFixed(4)}%</span></span>
        <a
          href={`https://v2.info.uniswap.org/pair/${position.pair_address}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-400 hover:text-indigo-300 transition-colors num"
        >
          {shortenAddress(position.pair_address)} ↗
        </a>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------
// V3 Position Card
// ---------------------------------------------------------------
function V3PositionCard({ position }: { position: UniswapV3Position }) {
  const hasFeesEarned = position.fees0_earned > 0 || position.fees1_earned > 0

  return (
    <div className="glass-card-inner p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <div
            className="px-2.5 py-1 rounded-lg text-xs font-bold"
            style={{
              background: 'rgba(168,85,247,0.15)',
              color: '#a78bfa',
              border: '1px solid rgba(168,85,247,0.2)',
            }}
          >
            V3
          </div>
          <span className="font-semibold text-slate-200">
            {position.token0_symbol}/{position.token1_symbol}
          </span>
          <span
            className="text-xs px-1.5 py-0.5 rounded num"
            style={{
              background: 'rgba(99,102,241,0.1)',
              color: '#818cf8',
            }}
          >
            {formatFeeTier(position.fee_tier)}
          </span>

          {/* In range / Out of range badge */}
          {position.in_range ? (
            <span className="badge-in-range">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block animate-pulse" />
              IN RANGE
            </span>
          ) : (
            <span className="badge-out-of-range">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block" />
              OUT OF RANGE
            </span>
          )}
        </div>
        <span className="num font-bold text-slate-200">{formatUSD(position.total_usd)}</span>
      </div>

      {/* Token amounts */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-2.5 rounded-lg" style={{ background: 'rgba(10,10,15,0.5)' }}>
          <p className="text-xs text-slate-500 mb-1">{position.token0_symbol}</p>
          <p className="num text-sm font-semibold text-slate-200">
            {formatAmount(position.token0_amount)}
          </p>
        </div>
        <div className="p-2.5 rounded-lg" style={{ background: 'rgba(10,10,15,0.5)' }}>
          <p className="text-xs text-slate-500 mb-1">{position.token1_symbol}</p>
          <p className="num text-sm font-semibold text-slate-200">
            {formatAmount(position.token1_amount)}
          </p>
        </div>
      </div>

      {/* Earned fees */}
      {hasFeesEarned && (
        <div
          className="p-3 rounded-lg flex items-center justify-between"
          style={{
            background: 'rgba(34,197,94,0.06)',
            border: '1px solid rgba(34,197,94,0.15)',
          }}
        >
          <span className="text-xs text-green-400 font-medium">Uncollected Fees</span>
          <div className="text-xs num space-x-2">
            {position.fees0_earned > 0 && (
              <span className="text-green-300">
                {formatAmount(position.fees0_earned)} {position.token0_symbol}
              </span>
            )}
            {position.fees1_earned > 0 && (
              <span className="text-green-300">
                {formatAmount(position.fees1_earned)} {position.token1_symbol}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Tick info */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>
          Ticks:{' '}
          <span className="num text-slate-400">
            [{position.tick_lower} → {position.tick_upper}]
          </span>{' '}
          Current:{' '}
          <span className="num text-slate-400">{position.current_tick}</span>
        </span>
        <span className="num text-slate-600">#{position.token_id}</span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------
// Skeleton card
// ---------------------------------------------------------------
function SkeletonCard() {
  return (
    <div className="glass-card-inner p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="skeleton w-10 h-6 rounded-lg" />
          <div className="skeleton w-24 h-5 rounded" />
        </div>
        <div className="skeleton w-20 h-5 rounded" />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="skeleton h-16 rounded-lg" />
        <div className="skeleton h-16 rounded-lg" />
      </div>
      <div className="skeleton w-48 h-3 rounded" />
    </div>
  )
}

// ---------------------------------------------------------------
// Main component
// ---------------------------------------------------------------
export default function LiquidityPositions({ liquidity, isLoading }: LiquidityPositionsProps) {
  const totalPositions = liquidity.v2_positions.length + liquidity.v3_positions.length

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <svg
            className="w-4 h-4 text-amber-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
          </svg>
          <h3 className="font-semibold text-slate-200">Liquidity Positions</h3>
          {!isLoading && (
            <span
              className="text-xs px-2 py-0.5 rounded-full num"
              style={{
                background: 'rgba(245,158,11,0.15)',
                color: '#fbbf24',
                border: '1px solid rgba(245,158,11,0.2)',
              }}
            >
              {totalPositions}
            </span>
          )}
        </div>
        {!isLoading && (
          <span className="num text-sm font-semibold text-slate-300">
            {formatUSD(liquidity.total_usd)}
          </span>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Loading skeletons */}
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && totalPositions === 0 && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center mb-3"
              style={{ background: 'rgba(245,158,11,0.08)' }}
            >
              <svg
                className="w-6 h-6 text-slate-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
              </svg>
            </div>
            <p className="text-sm text-slate-500">No liquidity positions found</p>
            <p className="text-xs text-slate-600 mt-1">
              Uniswap V2 and V3 positions will appear here
            </p>
          </div>
        )}

        {/* V2 Positions */}
        {!isLoading && liquidity.v2_positions.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2 px-1">
              Uniswap V2
            </h4>
            <div className="space-y-2">
              {liquidity.v2_positions.map((pos) => (
                <V2PositionCard key={pos.pair_address} position={pos} />
              ))}
            </div>
          </div>
        )}

        {/* V3 Positions */}
        {!isLoading && liquidity.v3_positions.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2 px-1">
              Uniswap V3
            </h4>
            <div className="space-y-2">
              {liquidity.v3_positions.map((pos) => (
                <V3PositionCard key={pos.token_id} position={pos} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
