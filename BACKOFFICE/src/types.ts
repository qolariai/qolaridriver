// Formas devolvidas por /api/* (BACKEND/console/serial.py). Dinheiro em cêntimos, datas em epoch s.

export type Role = 'admin' | 'operator' | 'finance'
export type Admin = { id: number; email: string; name: string; role: Role; active: boolean; created_at: number; last_login_at: number | null }

export type TripState = 'requested' | 'accepted' | 'arrived' | 'in_progress' | 'completed' | 'cancelled' | 'no_drivers'
export type DriverStatus = 'pending' | 'approved' | 'suspended' | 'rejected'
export type Availability = 'offline' | 'online' | 'on_trip'
export type AppName = 'rider' | 'driver' | 'fleet'

export type Ref = { id: number; name: string }
export type PersonShort = { id: number; uuid: string; name: string; phone: string; rating: number }
export type VehicleShort = { id: number; uuid: string; label: string; plate: string; make: string; model: string; color: string; color_hex: string }

export type Driver = {
  id: number; uuid: string; first_name: string; last_name: string; name: string; phone: string; email: string
  license_number: string; status: DriverStatus; availability: Availability; org: Ref | null; city_id: number | null
  vehicle: VehicleShort | null; lat: number | null; lng: number | null; heading: number; location_at: number | null
  rating: number; rating_count: number; offers_received: number; offers_accepted: number; acceptance_rate: number | null
  created_at: number; last_seen_at: number | null; online_since: number | null; simulated: boolean; balance: number | null
}

export type Doc = {
  id: number; uuid: string; owner_type: 'driver' | 'vehicle'; owner_id: number; owner_name: string; kind: string
  number: string; expires_on: string | null; status: 'pending' | 'approved' | 'rejected'; has_file: boolean
  notes: string; reviewed_by: string; reviewed_at: number | null; created_at: number
}

export type Session = { id: string; app: AppName; subject_uuid: string; subject_name?: string; created_at: number; last_used_at: number; ip: string; user_agent: string; revoked: boolean }
export type Device = { id: number; app: AppName; device_key: string; subject_uuid: string | null; subject_name?: string; model: string; os_version: string; app_version: string; has_push_token: boolean; ip: string; first_seen_at: number; last_seen_at: number }

export type TripRow = {
  id: number; uuid: string; state: TripState; product: Ref; rider: PersonShort | null; driver: PersonShort | null
  pickup_address: string; dropoff_address: string; est_fare: number; fare: number | null; payment_method: 'cash' | 'card'
  requested_at: number; completed_at: number | null; cancelled_at: number | null; org: { id: number } | null; source: string
}

export type Offer = { id: number; uuid: string; driver: PersonShort; state: string; pickup_distance_m: number; pickup_eta_s: number; created_at: number; expires_at: number; responded_at: number | null }
export type TripEvent = { id: number; at: number; kind: string; actor: string; detail: string }
export type Ledger = { id: number; at: number; party: string; party_id: number | null; kind: string; amount: number; trip_id: number | null; payout_id: number | null; note: string; trip_uuid?: string | null }

export type Quote = {
  distance_m: number; duration_s: number; base: number; distance: number; time: number; minimum_applied: boolean
  surge: number; surge_amount: number; booking_fee: number; subtotal: number; discount: number; total: number
}

export type Trip = TripRow & {
  city: string; currency: string; vehicle: VehicleShort | null; pickup: { lat: number; lng: number }
  dropoff: { lat: number; lng: number } | null; est_distance_m: number; est_duration_s: number
  distance_m: number | null; duration_s: number | null; surge: number; discount: number; pin: string
  breakdown: { estimate?: Quote; final?: Quote; cancel_fee?: number }; cancelled_by: string; cancel_reason: string
  rider_to_driver_rating: number | null; driver_to_rider_rating: number | null; rider_comment: string
  accepted_at: number | null; arrived_at: number | null; started_at: number | null
  driver_live: { lat: number | null; lng: number | null; heading: number } | null
  events: TripEvent[]; offers: Offer[]; ledger: Ledger[]
}

export type Rider = PersonShort & {
  first_name: string; last_name: string; email: string; status: 'active' | 'blocked'; rating_count: number
  default_payment: 'cash' | 'card'; lat: number | null; lng: number | null; created_at: number; last_seen_at: number | null
  trips?: number
}

export type Fleet = {
  id: number; uuid: string; name: string; tax_id: string; email: string; phone: string; city_id: number | null
  fleet_fee_pct: number; iban: string; status: 'active' | 'suspended'; created_at: number
  drivers_count: number; vehicles_count: number; online_count: number; balance?: number
}
export type FleetUser = { id: number; uuid: string; org_id: number; first_name: string; last_name: string; phone: string; email: string; role: string; active: boolean; created_at: number; last_seen_at: number | null }

export type Vehicle = VehicleShort & {
  year: number; vin: string; seats: number; status: 'pending' | 'active' | 'inactive'; product_ids: number[]
  org: Ref | null; owner_driver_id: number | null; created_at: number; drivers: { id: number; name: string }[]
}

export type City = { id: number; uuid: string; name: string; country_iso2: string; currency: string; timezone: string; center_lat: number; center_lng: number; radius_km: number; active: boolean }
export type Product = {
  id: number; uuid: string; city_id: number; code: string; name: string; description: string; capacity: number
  base_fare: number; per_km: number; per_min: number; minimum_fare: number; booking_fee: number; cancel_fee: number
  surge: number; min_vehicle_year: number; sort_order: number; active: boolean
}
export type Promo = {
  id: number; code: string; description: string; kind: 'percent' | 'amount'; value: number; max_discount: number | null
  max_uses: number | null; per_rider: number; uses: number; product_id: number | null; valid_from: number | null
  valid_to: number | null; active: boolean; created_at: number
}
export type Payout = { id: number; uuid: string; party: 'driver' | 'fleet'; party_id: number; party_name: string; amount: number; status: 'pending' | 'paid' | 'cancelled'; reference: string; created_at: number; paid_at: number | null }
