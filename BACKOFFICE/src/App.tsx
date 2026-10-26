import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, LiveProvider, useAuth } from './live'
import { Account } from './pages/Account'
import { Adjustments } from './pages/Adjustments'
import { Dashboard } from './pages/Dashboard'
import { Documents } from './pages/Documents'
import { DriverPage } from './pages/DriverPage'
import { Drivers } from './pages/Drivers'
import { Finance } from './pages/Finance'
import { FleetPage } from './pages/FleetPage'
import { Fleets } from './pages/Fleets'
import { Integration, IntegrationApp } from './pages/Integration'
import { Login } from './pages/Login'
import { MapReports } from './pages/MapReports'
import { Pricing } from './pages/Pricing'
import { Promos } from './pages/Promos'
import { RiderPage, Riders } from './pages/Riders'
import { Safety } from './pages/Safety'
import { Settings } from './pages/Settings'
import { Simulator } from './pages/Simulator'
import { Support } from './pages/Support'
import { TripPage } from './pages/TripPage'
import { Trips } from './pages/Trips'
import { Vehicles } from './pages/Vehicles'
import { Shell } from './ui/Shell'
import { Loading, ToastProvider } from './ui/kit'

function Gate() {
  const { user, ready } = useAuth()
  if (!ready) return <div className="center"><Loading /></div>
  if (!user) return <Login />
  return (
    <LiveProvider>
      <Routes>
        <Route element={<Shell />}>
          <Route index element={<Dashboard />} />
          <Route path="viagens" element={<Trips />} />
          <Route path="viagens/:id" element={<TripPage />} />
          <Route path="simulador" element={<Simulator />} />
          <Route path="motoristas" element={<Drivers />} />
          <Route path="motoristas/:id" element={<DriverPage />} />
          <Route path="passageiros" element={<Riders />} />
          <Route path="passageiros/:id" element={<RiderPage />} />
          <Route path="frotas" element={<Fleets />} />
          <Route path="frotas/:id" element={<FleetPage />} />
          <Route path="veiculos" element={<Vehicles />} />
          <Route path="documentos" element={<Documents />} />
          <Route path="tarifas" element={<Pricing />} />
          <Route path="promocoes" element={<Promos />} />
          <Route path="financas" element={<Finance />} />
          <Route path="ajustes" element={<Adjustments />} />
          <Route path="integracao" element={<Integration />} />
          <Route path="integracao/:app" element={<IntegrationApp />} />
          <Route path="mapa-problemas" element={<MapReports />} />
          <Route path="suporte" element={<Support />} />
          <Route path="seguranca" element={<Safety />} />
          <Route path="definicoes" element={<Settings />} />
          <Route path="conta" element={<Account />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </LiveProvider>
  )
}

export function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Gate />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
