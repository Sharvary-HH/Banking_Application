import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import AccountHistory from './pages/AccountHistory'
import AccountTransfer from './pages/AccountTransfer'
import Analytics from './pages/Analytics'
import Beneficiaries from './pages/Beneficiaries'
import Dashboard from './pages/Dashboard'
import Loans from './pages/Loans'
import Login from './pages/Login'
import Register from './pages/Register'
import ScheduledTransfers from './pages/ScheduledTransfers'
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
      <Route
        path="/beneficiaries"
        element={
          <ProtectedRoute>
            <Beneficiaries />
          </ProtectedRoute>
        }
      />
      <Route
        path="/scheduled-transfers"
        element={
          <ProtectedRoute>
            <ScheduledTransfers />
          </ProtectedRoute>
        }
      />
      <Route
        path="/loans"
        element={
          <ProtectedRoute>
            <Loans />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <Analytics />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
