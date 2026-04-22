import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../lib/auth'

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { tokens } = useAuth()
  const location = useLocation()
  if (!tokens) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }
  return children
}

