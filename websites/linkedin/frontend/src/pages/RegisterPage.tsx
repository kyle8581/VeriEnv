import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../lib/auth'

export function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
          <div className="text-[28px] font-semibold">Join LinkedIn</div>
          <div className="text-[14px] text-black/60 mt-1">Make the most of your professional life.</div>

          <form
            className="mt-5 space-y-3"
            onSubmit={async (e) => {
              e.preventDefault()
              setSubmitting(true)
              setError(null)
              try {
                await register({ email, password, first_name: firstName, last_name: lastName })
                navigate('/feed', { replace: true })
              } catch (err: any) {
                setError(err?.message ?? 'Registration failed')
              } finally {
                setSubmitting(false)
              }
            }}
          >
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[12px] text-black/60 mb-1">First name</label>
                <input
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full h-12 rounded border border-black/30 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/30 focus:border-[#0a66c2]"
                />
              </div>
              <div>
                <label className="block text-[12px] text-black/60 mb-1">Last name</label>
                <input
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full h-12 rounded border border-black/30 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/30 focus:border-[#0a66c2]"
                />
              </div>
            </div>
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
                autoComplete="new-password"
              />
            </div>

            {error ? <div className="text-[13px] text-[#b24020]">{error}</div> : null}

            <button
              type="submit"
              disabled={submitting}
              className="w-full h-12 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182] disabled:opacity-60 disabled:hover:bg-[#0a66c2]"
            >
              {submitting ? 'Creating account…' : 'Agree & Join'}
            </button>
          </form>

          <div className="mt-4 text-[13px] text-black/70">
            Already on LinkedIn?{' '}
            <Link to="/login" className="text-[#0a66c2] font-semibold hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

