import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import AccountHistory from './pages/AccountHistory'
import AccountTransfer from './pages/AccountTransfer'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import TwoFASetup from './pages/TwoFASetup'
import TwoFAVerify from './pages/TwoFAVerify'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/login/2fa" element={<TwoFAVerify />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings/2fa"
        element={
          <ProtectedRoute>
            <TwoFASetup />
          </ProtectedRoute>
        }
      />
      <Route
        path="/accounts/:id/transfer"
        element={
          <ProtectedRoute>
            <AccountTransfer />
          </ProtectedRoute>
        }
      />
      <Route
        path="/accounts/:id/history"
        element={
          <ProtectedRoute>
            <AccountHistory />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
