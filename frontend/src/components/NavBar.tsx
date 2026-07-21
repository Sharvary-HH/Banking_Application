import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const linkClasses = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-brand-500/15 text-brand-400' : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
  }`

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <header className="border-b border-zinc-800 bg-black">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="text-lg font-bold text-brand-400">Banking App</span>
          <nav className="flex items-center gap-1">
            <NavLink to="/dashboard" className={linkClasses}>
              Dashboard
            </NavLink>
            <NavLink to="/beneficiaries" className={linkClasses}>
              Beneficiaries
            </NavLink>
            <NavLink to="/scheduled-transfers" className={linkClasses}>
              Scheduled Transfers
            </NavLink>
            <NavLink to="/loans" className={linkClasses}>
              Loans
            </NavLink>
            <NavLink to="/settings/2fa" className={linkClasses}>
              2FA Setup
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-zinc-400">
              {user.email} <span className="text-zinc-600">·</span>{' '}
              <span className="font-medium text-zinc-300">{user.role}</span>
            </span>
          )}
          <button type="button" onClick={handleLogout} className="btn-secondary">
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}
