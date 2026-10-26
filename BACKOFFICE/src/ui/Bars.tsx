// Gráfico de barras simples em SVG (sem biblioteca). Valores >= 0.
import { useState } from 'react'

export function Bars({ data, format, height = 180 }: {
  data: { label: string; value: number; sub?: string }[]
  format: (v: number) => string
  height?: number
}) {
  const [hover, setHover] = useState<number | null>(null)
  const max = Math.max(1, ...data.map((d) => d.value))
  const n = data.length
  const gap = 6
  const w = 100 / n
  const ticks = [0, 0.5, 1].map((f) => max * f)
  return (
    <div className="bars" style={{ height }}>
      <div className="bars-grid">
        {ticks.slice().reverse().map((t) => <span key={t}>{format(t)}</span>)}
      </div>
      <svg viewBox={`0 0 100 ${height}`} preserveAspectRatio="none" role="img" aria-label="gráfico">
        {[0, 0.5, 1].map((f) => (
          <line key={f} x1="0" x2="100" y1={height - 22 - f * (height - 34)} y2={height - 22 - f * (height - 34)} className="bars-line" vectorEffect="non-scaling-stroke" />
        ))}
        {data.map((d, i) => {
          const h = (d.value / max) * (height - 34)
          return (
            <rect key={i} x={i * w + gap / n} width={w - (2 * gap) / n} y={height - 22 - h} height={Math.max(h, d.value ? 1.5 : 0)} rx="0.8"
              className={`bars-bar ${hover === i ? 'on' : ''}`} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} />
          )
        })}
      </svg>
      <div className="bars-labels">
        {data.map((d, i) => <span key={i} style={{ width: `${w}%` }}>{n > 10 && i % 2 ? '' : d.label}</span>)}
      </div>
      {hover !== null && (
        <div className="bars-tip" style={{ left: `${(hover + 0.5) * w}%` }}>
          <strong>{format(data[hover].value)}</strong>
          <span>{data[hover].label}{data[hover].sub ? ` · ${data[hover].sub}` : ''}</span>
        </div>
      )}
    </div>
  )
}
