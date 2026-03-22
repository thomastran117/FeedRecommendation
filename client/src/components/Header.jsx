import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Header() {
  const { accessToken, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="text-sm font-semibold text-gray-900 tracking-tight">
          Newsly
        </Link>

        <nav className="flex items-center gap-6">
          {accessToken ? (
            <>
              <Link
                to="/search"
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Search
              </Link>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Sign in
              </Link>
              <Link
                to="/signup"
                className="text-sm font-medium text-white bg-gray-900 hover:bg-gray-700 px-3 py-1.5 rounded-md transition-colors"
              >
                Create account
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
