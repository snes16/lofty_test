import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
}

export default function GridBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationId: number
    let mouseX = -9999
    let mouseY = -9999
    let particles: Particle[] = []

    const MAX_DIST = 140
    const MOUSE_REPEL_DIST = 100
    const MAX_SPEED = 0.6
    const PARTICLE_COLOR = '99, 102, 241'
    const PARTICLE_COLOR_ALT = '139, 92, 246'

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    const initParticles = () => {
      const count = Math.min(
        Math.floor((canvas.width * canvas.height) / 14000),
        90,
      )
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 1.5 + 0.5,
      }))
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Update particles
      for (const p of particles) {
        // Mouse repulsion
        const dx = p.x - mouseX
        const dy = p.y - mouseY
        const distSq = dx * dx + dy * dy
        if (distSq < MOUSE_REPEL_DIST * MOUSE_REPEL_DIST) {
          const dist = Math.sqrt(distSq)
          const force = ((MOUSE_REPEL_DIST - dist) / MOUSE_REPEL_DIST) * 0.025
          p.vx += (dx / dist) * force
          p.vy += (dy / dist) * force
        }

        // Velocity damping
        p.vx *= 0.98
        p.vy *= 0.98

        // Speed clamp
        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
        if (speed > MAX_SPEED) {
          p.vx = (p.vx / speed) * MAX_SPEED
          p.vy = (p.vy / speed) * MAX_SPEED
        }

        p.x += p.vx
        p.y += p.vy

        // Wrap around edges
        if (p.x < 0) p.x = canvas.width
        else if (p.x > canvas.width) p.x = 0
        if (p.y < 0) p.y = canvas.height
        else if (p.y > canvas.height) p.y = 0
      }

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const distSq = dx * dx + dy * dy

          if (distSq < MAX_DIST * MAX_DIST) {
            const dist = Math.sqrt(distSq)
            const opacity = (1 - dist / MAX_DIST) * 0.35
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(${PARTICLE_COLOR}, ${opacity})`
            ctx.lineWidth = 0.6
            ctx.stroke()
          }
        }
      }

      // Draw particles
      for (const p of particles) {
        const dxM = p.x - mouseX
        const dyM = p.y - mouseY
        const nearMouse = dxM * dxM + dyM * dyM < MOUSE_REPEL_DIST * MOUSE_REPEL_DIST

        const color = nearMouse ? PARTICLE_COLOR_ALT : PARTICLE_COLOR
        const alpha = nearMouse ? 0.9 : 0.55
        const r = nearMouse ? p.radius * 1.6 : p.radius

        // Glow
        const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 4)
        gradient.addColorStop(0, `rgba(${color}, ${alpha})`)
        gradient.addColorStop(1, `rgba(${color}, 0)`)
        ctx.beginPath()
        ctx.arc(p.x, p.y, r * 4, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.fill()

        // Core dot
        ctx.beginPath()
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${color}, ${alpha})`
        ctx.fill()
      }

      animationId = requestAnimationFrame(draw)
    }

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX
      mouseY = e.clientY
    }

    const handleMouseLeave = () => {
      mouseX = -9999
      mouseY = -9999
    }

    const handleResize = () => {
      resize()
      initParticles()
    }

    resize()
    initParticles()
    draw()

    window.addEventListener('resize', handleResize)
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  )
}
