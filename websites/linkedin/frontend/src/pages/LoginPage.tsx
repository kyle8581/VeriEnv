import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../lib/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()

  const [email, setEmail] = useState('jane.doe@example.com')
  const [password, setPassword] = useState('password123')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const from = (location.state as any)?.from as string | undefined

  return (
    <div className="min-h-full bg-[#f3f2ef]">
      <div className="mx-auto max-w-[1128px] px-3 pt-10">
        <div className="flex items-center gap-2">
          <div className="h-10 w-10 rounded bg-[#0a66c2] text-white flex items-center justify-center font-bold leading-none">
            in
          </div>
          <div className="text-[20px] font-semibold text-black/80">linkedin</div>
        </div>
      </div>

      <div className="mx-auto max-w-[420px] px-3 pt-8">
        <div className="bg-white border border-black/10 rounded-lg p-6 shadow-sm">
          <div className="text-[28px] font-semibold">Sign in</div>
          <div className="text-[14px] text-black/60 mt-1">Stay updated on your professional world.</div>

          <form
            className="mt-5 space-y-3"
            onSubmit={async (e) => {
              e.preventDefault()
              setSubmitting(true)
              setError(null)
              try {
                await login(email, password)
                navigate(from || '/feed', { replace: true })
              } catch (err: any) {
                setError(err?.message ?? 'Login failed')
              } finally {
                setSubmitting(false)
              }
            }}
          >
            <div>
              <label className="block text-[12px] text-black/60 mb-1">Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-12 rounded border border-black/30 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/30 focus:border-[#0a66c2]"
                autoComplete="email"
              />
            </div>
            <div>
              <label className="block text-[12px] text-black/60 mb-1">Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                className="w-full h-12 rounded border border-black/30 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/30 focus:border-[#0a66c2]"
                autoComplete="current-password"
              />
            </div>

            {error ? <div className="text-[13px] text-[#b24020]">{error}</div> : null}

            <button
              type="submit"
              disabled={submitting}
              className="w-full h-12 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182] disabled:opacity-60 disabled:hover:bg-[#0a66c2]"
            >
              {submitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="mt-4 text-[13px] text-black/70">
            New to LinkedIn?{' '}
            <Link to="/register" className="text-[#0a66c2] font-semibold hover:underline">
              Join now
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

