import type { Availability, DriverStatus, TripState } from './types'

const eurFmt = new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' })
export const eur = (cents: number | null | undefined) => (cents == null ? '—' : eurFmt.format(cents / 100))

/** "9,50" | "9.5" | "9" -> 950 ; inválido -> null */
export function parseCents(text: string): number | null {
  const t = text.trim().replace(/\s|€/g, '').replace(',', '.')
  if (!/^-?\d+(\.\d{0,2})?$/.test(t)) return null
  return Math.round(parseFloat(t) * 100)
}
export const centsInput = (c: number | null | undefined) => (c == null ? '' : (c / 100).toFixed(2).replace('.', ','))

const dt = new Intl.DateTimeFormat('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
const tm = new Intl.DateTimeFormat('pt-PT', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
const dd = new Intl.DateTimeFormat('pt-PT', { day: '2-digit', month: 'short' })
export const dateTime = (s: number | null | undefined) => (s ? dt.format(new Date(s * 1000)) : '—')
export const clock = (s: number | null | undefined) => (s ? tm.format(new Date(s * 1000)) : '—')
export const dayLabel = (s: number) => dd.format(new Date(s * 1000))

export function ago(s: number | null | undefined): string {
  if (!s) return 'nunca'
  const d = Math.max(0, Math.round(Date.now() / 1000 - s))
  if (d < 60) return `há ${d} s`
  if (d < 3600) return `há ${Math.round(d / 60)} min`
  if (d < 86400) return `há ${Math.round(d / 3600)} h`
  return `há ${Math.round(d / 86400)} d`
}
export const km = (m: number | null | undefined) => (m == null ? '—' : `${(m / 1000).toFixed(1).replace('.', ',')} km`)
export const mins = (s: number | null | undefined) => (s == null ? '—' : s < 3600 ? `${Math.max(1, Math.round(s / 60))} min` : `${Math.floor(s / 3600)} h ${Math.round((s % 3600) / 60)} min`)
export const pct = (x: number | null | undefined) => (x == null ? '—' : `${Math.round(x * 100)}%`)
export const isoDay = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

export const TRIP_STATE: Record<TripState, string> = {
  requested: 'A procurar',
  accepted: 'A caminho',
  arrived: 'No local',
  in_progress: 'Em viagem',
  completed: 'Concluída',
  cancelled: 'Cancelada',
  no_drivers: 'Sem motoristas',
}
export const TRIP_TONE: Record<TripState, string> = {
  requested: 'warn', accepted: 'info', arrived: 'info', in_progress: 'accent', completed: 'ok', cancelled: 'muted', no_drivers: 'bad',
}
export const DRIVER_STATUS: Record<DriverStatus, string> = { pending: 'Em verificação', approved: 'Aprovado', suspended: 'Suspenso', rejected: 'Recusado' }
export const DRIVER_TONE: Record<DriverStatus, string> = { pending: 'warn', approved: 'ok', suspended: 'bad', rejected: 'muted' }
export const AVAIL: Record<Availability, string> = { offline: 'Offline', online: 'Disponível', on_trip: 'Em viagem' }
export const AVAIL_TONE: Record<Availability, string> = { offline: 'muted', online: 'ok', on_trip: 'accent' }

export const EVENT: Record<string, string> = {
  requested: 'Pedido', offer: 'Proposta enviada', offer_rejected: 'Proposta recusada', offer_expired: 'Proposta expirou',
  accepted: 'Aceite', arrived: 'Chegou à recolha', started: 'Viagem iniciada', completed: 'Concluída', cancelled: 'Cancelada',
  no_drivers: 'Sem motoristas', rated: 'Avaliação', forced: 'Estado forçado',
}
export const ACTOR: Record<string, string> = { rider: 'Passageiro', driver: 'Motorista', admin: 'Consola', system: 'Sistema', fleet: 'Frota' }
export const LEDGER_KIND: Record<string, string> = {
  fare: 'Tarifa', commission: 'Comissão', fleet_fee: 'Taxa de frota', cash_collected: 'Recebido em dinheiro',
  cancel_fee: 'Taxa de cancelamento', promo: 'Promoção', payout: 'Pagamento', adjustment: 'Acerto',
}
export const PARTY: Record<string, string> = { driver: 'Motorista', fleet: 'Frota', platform: 'Plataforma', rider: 'Passageiro' }
export const APP_LABEL = { rider: 'Rider', driver: 'Driver', fleet: 'Fleet' } as const
export const DOC_KIND: Record<string, string> = {
  carta_conducao: 'Carta de condução', cartao_cidadao: 'Cartão de cidadão', certificado_tvde: 'Certificado TVDE',
  registo_criminal: 'Registo criminal', atestado_medico: 'Atestado médico', dua: 'DUA', seguro: 'Seguro',
  inspecao: 'Inspeção periódica', licenca_tvde: 'Licença TVDE',
}
