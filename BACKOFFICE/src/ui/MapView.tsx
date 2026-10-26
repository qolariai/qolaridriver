// Mapa Leaflet com mosaicos OpenStreetMap (precisa de internet para os mosaicos; os marcadores
// funcionam sem eles). Marcadores desenhados em SVG para não depender de imagens.
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'

export type MapDriver = { id: number; name: string; lat: number; lng: number; heading: number; availability: string; vehicle?: string | null }
export type MapTrip = { uuid: string; state: string; pickup: [number, number]; dropoff: [number, number] | null; label?: string }

const COLOR: Record<string, string> = { online: '#16a34a', on_trip: '#7c3aed', offline: '#94a3b8' }

function carIcon(d: MapDriver, selected: boolean) {
  const c = COLOR[d.availability] ?? '#64748b'
  const size = selected ? 34 : 28
  return L.divIcon({
    className: 'map-car',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    html: `<svg viewBox="0 0 32 32" width="${size}" height="${size}" style="transform:rotate(${d.heading || 0}deg)">
      <circle cx="16" cy="16" r="13" fill="${c}" stroke="white" stroke-width="${selected ? 4 : 3}"/>
      <path d="M16 7l5 12-5-3-5 3z" fill="white"/></svg>`,
  })
}

const dot = (color: string, letter: string) =>
  L.divIcon({
    className: 'map-pin',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    html: `<div style="width:24px;height:24px;border-radius:50%;background:${color};color:#fff;font:700 12px system-ui;display:grid;place-items:center;border:2px solid #fff;box-shadow:0 1px 4px #0005">${letter}</div>`,
  })

export function MapView({ center, drivers = [], trips = [], height = 420, selectedDriver, onDriverClick, onMapClick, extra, fit }: {
  center: [number, number]
  drivers?: MapDriver[]
  trips?: MapTrip[]
  height?: number | string
  selectedDriver?: number | null
  onDriverClick?: (id: number) => void
  onMapClick?: (lat: number, lng: number) => void
  extra?: { lat: number; lng: number; color: string; letter: string }[]
  fit?: boolean
}) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<L.Map | null>(null)
  const layer = useRef<L.LayerGroup | null>(null)
  const clickRef = useRef(onMapClick)
  clickRef.current = onMapClick
  const driverClickRef = useRef(onDriverClick)
  driverClickRef.current = onDriverClick
  const fitted = useRef(false)

  useEffect(() => {
    if (!el.current || map.current) return
    const m = L.map(el.current, { zoomControl: true, attributionControl: true }).setView(center, 12)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap',
    }).addTo(m)
    m.on('click', (e: L.LeafletMouseEvent) => clickRef.current?.(e.latlng.lat, e.latlng.lng))
    layer.current = L.layerGroup().addTo(m)
    map.current = m
    const ro = new ResizeObserver(() => m.invalidateSize())
    ro.observe(el.current)
    return () => {
      ro.disconnect()
      m.remove()
      map.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const g = layer.current
    if (!g) return
    g.clearLayers()
    const pts: L.LatLngExpression[] = []
    for (const t of trips) {
      L.marker(t.pickup, { icon: dot('#0ea5e9', 'A') }).bindTooltip(t.label ?? 'Recolha').addTo(g)
      pts.push(t.pickup)
      if (t.dropoff) {
        L.marker(t.dropoff, { icon: dot('#111827', 'B') }).bindTooltip('Destino').addTo(g)
        L.polyline([t.pickup, t.dropoff], { color: '#0ea5e9', weight: 3, dashArray: '6 6', opacity: 0.8 }).addTo(g)
        pts.push(t.dropoff)
      }
    }
    for (const d of drivers) {
      const mk = L.marker([d.lat, d.lng], { icon: carIcon(d, d.id === selectedDriver), zIndexOffset: 500 })
        .bindTooltip(`${d.name}${d.vehicle ? ` · ${d.vehicle}` : ''}`)
        .addTo(g)
      mk.on('click', () => driverClickRef.current?.(d.id))
      pts.push([d.lat, d.lng])
    }
    for (const x of extra ?? []) {
      L.marker([x.lat, x.lng], { icon: dot(x.color, x.letter), zIndexOffset: 900 }).addTo(g)
      pts.push([x.lat, x.lng])
    }
    if (fit && !fitted.current && pts.length > 1 && map.current) {
      map.current.fitBounds(L.latLngBounds(pts), { padding: [40, 40], maxZoom: 15 })
      fitted.current = true
    }
  }, [drivers, trips, selectedDriver, extra, fit])

  return <div ref={el} className="map" style={{ height }} />
}
