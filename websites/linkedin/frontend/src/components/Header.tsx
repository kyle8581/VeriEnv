import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, NavLink, useNavigate, useSearchParams } from 'react-router-dom'

import { apiFetch } from '../lib/api'
import { useAuth } from '../lib/auth'

function cx(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(' ')
}

function LinkedInLogo() {
  return (
    <div className="flex items-center gap-2">
      <div className="h-9 w-9 rounded bg-[#0a66c2] text-white flex items-center justify-center font-bold leading-none">
        in
      </div>
    </div>
  )
}

function Icon({ name }: { name: 'home' | 'network' | 'jobs' | 'message' | 'notif' | 'me' | 'grid' }) {
  const common = { className: 'h-6 w-6', fill: 'none', stroke: 'currentColor', strokeWidth: 1.7 }
  switch (name) {
    case 'home':
      return (
        <svg viewBox="0 0 24 24" {...common}>
          <path d="M3 10.5 12 3l9 7.5" />
          <path d="M6.5 10.5V21h11V10.5" />
        </svg>
      )
    case 'network':
      return (
        <svg viewBox="0 0 24 24" {...common}>
          <path d="M16 11a3 3 0 1 0-6 0" />
          <path d="M4 20a6 6 0 0 1 12 0" />
          <path d="M18.5 20a4.5 4.5 0 0 1 1.5-3.4" />
          <path d="M20 11.5a2.5 2.5 0 1 0-3.6-2.2" />
        </svg>
      )
    case 'jobs':
      return (
        <svg viewBox="0 0 24 24" {...common}>
          <path d="M8 7V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1" />
          <path d="M4 7h16v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7Z" />
          <path d="M4 12h16" />
        </svg>
      )
    case 'message':
      return (
        <svg viewBox="0 0 24 24" {...common}>
          <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z" />
        </svg>
      )
    case 'notif':
      return (
        <svg viewBox="0 0 24 24" {...common}>
          <path d="M18 8a6 6 0 1 0-12 0c0 7-3 7-3 7h18s-3 0-3-7" />
          <path d="M9.5 19a2.5 2.5 0 0 0 5 0" />
        </svg>
      )
    case 'grid':
      return (
        <svg viewBox="0 0 24 24" {...common}>
          <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" />
        </svg>
      )
    case 'me':
      return (
        <svg viewBox="0 0 24 24" {...common}>
          <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z" />
          <path d="M4 21a8 8 0 0 1 16 0" />
        </svg>
      )
  }
}

export function Header() {
  const navigate = useNavigate()
  const { me, logout, tokens } = useAuth()

  const [params] = useSearchParams()
  const qFromUrl = params.get('q') ?? ''

  const [q, setQ] = useState(qFromUrl)
  const [open, setOpen] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)
  const boxRef = useRef<HTMLDivElement | null>(null)
  const [meOpen, setMeOpen] = useState(false)

  useEffect(() => {
    setQ(qFromUrl)
  }, [qFromUrl])

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (!boxRef.current) return
      const t = e.target as Node
      if (!boxRef.current.contains(t)) setOpen(false)
      const meBox = document.getElementById('me-menu-box')
      if (meBox && !meBox.contains(t)) setMeOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  useEffect(() => {
    const term = q.trim()
    if (!open || term.length < 1) {
      setSuggestions([])
      return
    }
    const t = window.setTimeout(async () => {
      setLoading(true)
      try {
        const res = await apiFetch<{ suggestions: string[] }>(`/search/typeahead?q=${encodeURIComponent(term)}`, {
          accessToken: tokens?.access_token,
        })
        setSuggestions(res.suggestions ?? [])
      } finally {
        setLoading(false)
      }
    }, 120)
    return () => window.clearTimeout(t)
  }, [q, open])

  const items = useMemo(() => {
    const base = suggestions.length ? suggestions : q.trim() ? [q.trim()] : []
    return base.slice(0, 8)
  }, [suggestions, q])

  const submit = (term: string) => {
    const t = term.trim()
    if (!t) return
    setOpen(false)
    navigate(`/search?q=${encodeURIComponent(t)}`)
  }

  return (
    <div className="sticky top-0 z-50 bg-white border-b border-black/10">
      <div className="mx-auto max-w-[1128px] h-[52px] px-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Link to="/feed" aria-label="Home">
            <LinkedInLogo />
          </Link>

          <div ref={boxRef} className="relative">
            <div className="relative">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-black/60"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M21 21l-4.3-4.3" />
                <path d="M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z" />
              </svg>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onFocus={() => setOpen(true)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const term = activeIdx >= 0 ? items[activeIdx] : q
                    submit(term)
                  }
                  if (e.key === 'ArrowDown') {
                    e.preventDefault()
                    setActiveIdx((i) => Math.min(i + 1, items.length - 1))
                  }
                  if (e.key === 'ArrowUp') {
                    e.preventDefault()
                    setActiveIdx((i) => Math.max(i - 1, -1))
                  }
                  if (e.key === 'Escape') setOpen(false)
                }}
                placeholder="Search"
                className="w-[280px] h-[34px] rounded-md bg-[#edf3f8] pl-9 pr-3 text-[14px] outline-none focus:bg-white focus:ring-1 focus:ring-black/20"
              />
            </div>

            {open && (
              <div className="absolute left-0 right-0 mt-1 rounded-md bg-white border border-black/10 shadow-lg overflow-hidden">
                <div className="max-h-[320px] overflow-auto">
                  {loading && items.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-black/60">Searching…</div>
                  ) : (
                    <>
                      {items.map((s, idx) => (
                        <button
                          key={`${s}-${idx}`}
                          onMouseEnter={() => setActiveIdx(idx)}
                          onClick={() => submit(s)}
                          className={cx(
                            'w-full text-left px-3 py-2 text-[14px] flex items-center gap-2 hover:bg-black/5',
                            idx === activeIdx && 'bg-black/5',
                          )}
                        >
                          <span className="text-black/60">🔎</span>
                          <span className="truncate">{s}</span>
                        </button>
                      ))}
                      <button
                        onClick={() => submit(q)}
                        className="w-full text-left px-3 py-2 text-[14px] border-t border-black/10 hover:bg-black/5"
                      >
                        See all results
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <nav className="flex items-center gap-2 text-black/70">
          <NavLink to="/feed" className={({ isActive }) => cx('px-3 py-1', isActive && 'text-black')}>
            <div className="flex flex-col items-center leading-none">
              <Icon name="home" />
              <span className="text-[11px] mt-1">Home</span>
            </div>
          </NavLink>
          <NavLink to="/network" className={({ isActive }) => cx('px-3 py-1', isActive && 'text-black')}>
            <div className="flex flex-col items-center leading-none">
              <Icon name="network" />
              <span className="text-[11px] mt-1">My Network</span>
            </div>
          </NavLink>
          <NavLink to="/jobs" className={({ isActive }) => cx('px-3 py-1', isActive && 'text-black')}>
            <div className="flex flex-col items-center leading-none">
              <Icon name="jobs" />
              <span className="text-[11px] mt-1">Jobs</span>
            </div>
          </NavLink>
          <NavLink to="/messaging" className={({ isActive }) => cx('px-3 py-1', isActive && 'text-black')}>
            <div className="flex flex-col items-center leading-none relative">
              <Icon name="message" />
              <span className="text-[11px] mt-1">Messaging</span>
            </div>
          </NavLink>
          <NavLink to="/notifications" className={({ isActive }) => cx('px-3 py-1', isActive && 'text-black')}>
            <div className="flex flex-col items-center leading-none relative">
              <Icon name="notif" />
              <span className="text-[11px] mt-1">Notifications</span>
            </div>
          </NavLink>

          <div className="px-3 py-1 relative" id="me-menu-box">
            <button
              onClick={() => setMeOpen((v) => !v)}
              className="flex flex-col items-center leading-none text-black/70 hover:text-black"
              title="Account"
            >
              {me?.avatar_url ? <img src={me.avatar_url} className="h-6 w-6 rounded-full object-cover" /> : <Icon name="me" />}
              <span className="text-[11px] mt-1">Me</span>
            </button>
            {meOpen ? (
              <div className="absolute right-0 mt-2 w-[240px] rounded-lg bg-white border border-black/10 shadow-lg overflow-hidden">
                <div className="p-3 border-b border-black/10">
                  <div className="text-[13px] font-semibold">
                    {me ? `${me.first_name} ${me.last_name}` : 'Account'}
                  </div>
                  <div className="text-[12px] text-black/60">{me?.email ?? ''}</div>
                </div>
                <button
                  onClick={() => {
                    setMeOpen(false)
                    logout()
                  }}
                  className="w-full text-left px-3 py-2 text-[13px] font-semibold hover:bg-black/5"
                >
                  Sign out
                </button>
              </div>
            ) : null}
          </div>

          <div className="h-8 w-px bg-black/10" />

          <NavLink to="/work" className={({ isActive }) => cx('px-2 py-1 flex items-center gap-1', isActive && 'text-black')}>
            <Icon name="grid" />
            <span className="text-[11px] leading-none">Work</span>
          </NavLink>

          <Link to="/premium" className="text-[12px] text-[#915907] hover:underline ml-2">
            Try Premium for free
          </Link>
        </nav>
      </div>
    </div>
  )
}

