import { useState, FormEvent } from 'react'

interface AddressInputProps {
  onAnalyze: (address: string) => void
  isLoading: boolean
}

function isValidEthAddress(address: string): boolean {
  return /^0x[0-9a-fA-F]{40}$/.test(address)
}

// Well-known demo addresses for convenience
const DEMO_ADDRESSES = [
  { label: 'Vitalik', address: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045' },
  { label: 'Uniswap', address: '0x1a9C8182C09F50C8318d769245beA52c32BE35BC' },
]

export default function AddressInput({ onAnalyze, isLoading }: AddressInputProps) {
  const [address, setAddress] = useState('')
  const [touched, setTouched] = useState(false)

  const isValid = isValidEthAddress(address)
  const showError = touched && address.length > 0 && !isValid

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setTouched(true)
    if (isValid) {
      onAnalyze(address.trim())
    }
  }

  function handleDemoClick(demoAddress: string) {
    setAddress(demoAddress)
    setTouched(true)
    onAnalyze(demoAddress)
  }

  return (
    <div className="glass-card p-6 md:p-8">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-1">
          Enter Wallet Address
        </h2>
        <p className="text-sm text-slate-500">
          Enter any Ethereum address to view its portfolio
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={address}
              onChange={(e) => {
                setAddress(e.target.value.trim())
                setTouched(false)
              }}
              onBlur={() => setTouched(true)}
              placeholder="0x..."
              className="input-dark w-full pr-10"
              aria-label="Ethereum wallet address"
              aria-invalid={showError}
              disabled={isLoading}
              spellCheck={false}
              autoComplete="off"
            />
            {/* Checkmark icon when valid */}
            {isValid && (
              <svg
                className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            )}
          </div>

          <button
            type="submit"
            disabled={!isValid || isLoading}
            className="btn-accent flex items-center gap-2 min-w-[130px] justify-center"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Analyzing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                Analyze
              </>
            )}
          </button>
        </div>

        {/* Inline validation error */}
        {showError && (
          <p className="text-xs text-red-400 flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            Please enter a valid Ethereum address (0x followed by 40 hex characters)
          </p>
        )}
      </form>

      {/* Demo address shortcuts */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-600">Try:</span>
        {DEMO_ADDRESSES.map((demo) => (
          <button
            key={demo.address}
            onClick={() => handleDemoClick(demo.address)}
            disabled={isLoading}
            className="text-xs px-2.5 py-1 rounded-lg transition-all duration-150 disabled:opacity-50"
            style={{
              background: 'rgba(99, 102, 241, 0.08)',
              border: '1px solid rgba(99, 102, 241, 0.2)',
              color: '#818cf8',
            }}
          >
            {demo.label}
          </button>
        ))}
      </div>
    </div>
  )
}
