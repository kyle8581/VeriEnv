import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { RequireAuth } from './app/RequireAuth'
import { useAuth } from './lib/auth'
import { FeedPage } from './pages/FeedPage'
import { JobsPage } from './pages/JobsPage'
import { LoginPage } from './pages/LoginPage'
import { MessagingPage } from './pages/MessagingPage'
import { NetworkPage } from './pages/NetworkPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { PremiumPage } from './pages/PremiumPage'
import { RegisterPage } from './pages/RegisterPage'
import { SearchPage } from './pages/SearchPage'
import { WorkPage } from './pages/WorkPage'

function HomeRedirect() {
  const { tokens } = useAuth()
  return <Navigate to={tokens ? '/feed' : '/login'} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/feed"
          element={
            <RequireAuth>
              <FeedPage />
            </RequireAuth>
          }
        />
        <Route
          path="/search"
          element={
            <RequireAuth>
              <SearchPage />
            </RequireAuth>
          }
        />
        <Route
          path="/jobs"
          element={
            <RequireAuth>
              <JobsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/network"
          element={
            <RequireAuth>
              <NetworkPage />
            </RequireAuth>
          }
        />
        <Route
          path="/messaging"
          element={
            <RequireAuth>
              <MessagingPage />
            </RequireAuth>
          }
        />
        <Route
          path="/notifications"
          element={
            <RequireAuth>
              <NotificationsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/work"
          element={
            <RequireAuth>
              <WorkPage />
            </RequireAuth>
          }
        />
        <Route
          path="/premium"
          element={
            <RequireAuth>
              <PremiumPage />
            </RequireAuth>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
