import type { TokenBalance, TokensResponse } from '../types'

interface TokensTableProps {
  tokens: TokensResponse
  isLoading?: boolean
}

function TokenRow({ token }: { token: TokenBalance }) {
  const priceFormatted =
    token.price_usd > 0
      ? token.price_usd < 0.01
        ? `$${token.price_usd.toExponential(2)}`
        : `$${token.price_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`
      : '—'

  const balanceFormatted =
    token.balance >= 1000
      ? token.balance.toLocaleString('en-US', { maximumFractionDigits: 2 })
      : token.balance.toFixed(token.balance < 1 ? 6 : 4)

  const usdFormatted = `$${token.balance_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

  return (
    <tr className="hover-row border-t border-slate-800/50 transition-colors">
      {/* Token */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Logo / Fallback */}
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
            style={{
              background: 'rgba(99,102,241,0.15)',
              border: '1px solid rgba(99,102,241,0.2)',
              color: '#818cf8',
            }}
          >
            {token.logo_url ? (
              <img
                src={token.logo_url}
                alt={token.symbol}
                className="w-full h-full rounded-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement
                  target.style.display = 'none'
                  const parent = target.parentElement
                  if (parent) {
                    parent.textContent = token.symbol.slice(0, 2).toUpperCase()
                  }
                }}
              />
            ) : (
              token.symbol.slice(0, 2).toUpperCase()
            )}
          </div>

          <div>
            <p className="font-semibold text-slate-200 text-sm">{token.symbol}</p>
            <p className="text-xs text-slate-500 truncate max-w-[140px]" title={token.name}>
              {token.name}
            </p>
          </div>
        </div>
      </td>

      {/* Balance */}
      <td className="px-4 py-3 text-right">
        <span className="num text-sm text-slate-300">{balanceFormatted}</span>
      </td>

      {/* Price */}
      <td className="px-4 py-3 text-right hidden sm:table-cell">
        <span className="num text-sm text-slate-400">{priceFormatted}</span>
      </td>

      {/* USD Value */}
      <td className="px-4 py-3 text-right">
        <span className="num text-sm font-semibold text-slate-200">{usdFormatted}</span>
      </td>
    </tr>
  )
}

function SkeletonRow() {
  return (
    <tr className="border-t border-slate-800/50">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="skeleton w-8 h-8 rounded-full" />
          <div className="space-y-1.5">
            <div className="skeleton w-16 h-3 rounded" />
            <div className="skeleton w-24 h-2.5 rounded" />
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <div className="skeleton w-20 h-3 rounded ml-auto" />
      </td>
      <td className="px-4 py-3 text-right hidden sm:table-cell">
        <div className="skeleton w-16 h-3 rounded ml-auto" />
      </td>
      <td className="px-4 py-3 text-right">
        <div className="skeleton w-20 h-3 rounded ml-auto" />
      </td>
    </tr>
  )
}

export default function TokensTable({ tokens, isLoading }: TokensTableProps) {
  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
          </svg>
          <h3 className="font-semibold text-slate-200">Token Holdings</h3>
          {!isLoading && (
            <span
              className="text-xs px-2 py-0.5 rounded-full num"
              style={{
                background: 'rgba(99,102,241,0.15)',
                color: '#818cf8',
                border: '1px solid rgba(99,102,241,0.2)',
              }}
            >
              {tokens.tokens.length}
            </span>
          )}
        </div>
        {!isLoading && (
          <span className="num text-sm font-semibold text-slate-300">
            ${tokens.total_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        )}
      </div>

      {/* Empty state */}
      {!isLoading && tokens.tokens.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center mb-3"
            style={{ background: 'rgba(99,102,241,0.1)' }}
          >
            <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
            </svg>
          </div>
          <p className="text-sm text-slate-500">No token holdings found</p>
        </div>
      )}

      {/* Table */}
      {(isLoading || tokens.tokens.length > 0) && (
        <div className="overflow-x-auto">
          <div className="overflow-y-auto" style={{ maxHeight: '400px' }}>
            <table className="w-full">
              <thead className="sticky top-0 z-10" style={{ background: 'rgba(15,23,42,0.95)' }}>
                <tr>
                  <th className="px-4 py-2.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Token
                  </th>
                  <th className="px-4 py-2.5 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Balance
                  </th>
                  <th className="px-4 py-2.5 text-right text-xs font-medium text-slate-500 uppercase tracking-wider hidden sm:table-cell">
                    Price
                  </th>
                  <th className="px-4 py-2.5 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 4 }).map((_, i) => <SkeletonRow key={i} />)
                  : tokens.tokens.map((token) => (
                      <TokenRow key={token.contract_address} token={token} />
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
