import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Garage from './screens/Garage'
import Login from './screens/Login'
import VehicleDetail from './screens/VehicleDetail'
import { hasSession } from './auth'

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!hasSession()) return <Navigate to="/login" replace />
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Garage />
            </RequireAuth>
          }
        />
        <Route
          path="/vehicles/:id"
          element={
            <RequireAuth>
              <VehicleDetail />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
