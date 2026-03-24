import { useEffect, useRef } from 'react'

export default function GridBackground() {
  const glowRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!glowRef.current) return
      glowRef.current.style.background =
        `radial-gradient(700px circle at ${e.clientX}px ${e.clientY}px, rgba(99,102,241,0.07), transparent 40%)`
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      {/* Static grid lines */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(99,102,241,0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99,102,241,0.05) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
        }}
      />
      {/* Mouse glow that makes grid lines near cursor brighter */}
      <div ref={glowRef} className="absolute inset-0" />
    </div>
  )
}
