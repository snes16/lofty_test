import type { EthBalance } from '../types'

interface EthCardProps {
  eth: EthBalance
  isLoading?: boolean
}

function SkeletonLine({ width }: { width: string }) {
  return <div className={`skeleton h-5 rounded ${width}`} />
}

export default function EthCard({ eth, isLoading }: EthCardProps) {
  return (
    <div className="glass-card p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        {/* ETH logo */}
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
          style={{
            background: 'linear-gradient(135deg, #6366f120, #6366f140)',
            border: '1px solid rgba(99,102,241,0.3)',
          }}
        >
          <svg className="w-5 h-5 text-indigo-400" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L6 12l6 4 6-4-6-10zM6 13.5l6 3.5 6-3.5L12 21 6 13.5z" />
          </svg>
        </div>
        <div>
          <h3 className="font-semibold text-slate-200">Ethereum</h3>
          <p className="text-xs text-slate-500">ETH</p>
        </div>
      </div>

      {/* Balance rows */}
      {isLoading ? (
        <div className="space-y-3">
          <SkeletonLine width="w-32" />
          <SkeletonLine width="w-24" />
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-slate-500">Balance</span>
            <span className="num font-bold text-xl text-slate-100">
              {eth.balance_eth.toFixed(6)}
              <span className="text-sm font-normal text-slate-400 ml-1.5">ETH</span>
            </span>
          </div>

          <div className="flex items-baseline justify-between">
            <span className="text-sm text-slate-500">Value</span>
            <span className="num font-semibold text-lg text-indigo-300">
              ${eth.balance_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          {eth.balance_eth > 0 && (
            <div className="flex items-baseline justify-between">
              <span className="text-sm text-slate-500">Price</span>
              <span className="num text-sm text-slate-400">
                ${(eth.balance_usd / eth.balance_eth).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Footer address */}
      {!isLoading && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <p className="num text-xs text-slate-600 truncate" title={eth.address}>
            {eth.address}
          </p>
        </div>
      )}
    </div>
  )
}
