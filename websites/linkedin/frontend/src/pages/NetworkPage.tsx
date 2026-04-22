import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { PageShell } from '../components/PageShell'
import { apiFetch } from '../lib/api'
import { useAuth } from '../lib/auth'

type PeopleSearchItem = { id: string; first_name: string; last_name: string; headline: string; location: string; avatar_url: string }
type PeopleSearchResponse = { total: number; items: PeopleSearchItem[] }

function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white border border-black/10 rounded-lg overflow-hidden">{children}</div>
}

const KEY = 'linkedin_clone_connections'

export function NetworkPage() {
  const { tokens } = useAuth()
  const token = tokens!.access_token

  const [q, setQ] = useState('bio')
  const [connections, setConnections] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || '{}') as Record<string, boolean>
    } catch {
      return {}
    }
  })

  const people = useQuery({
    queryKey: ['network', 'people', q],
    queryFn: () => apiFetch<PeopleSearchResponse>(`/search/people?q=${encodeURIComponent(q)}&limit=12`, { accessToken: token }),
    enabled: q.trim().length > 0,
  })

  const save = (next: Record<string, boolean>) => {
    setConnections(next)
    localStorage.setItem(KEY, JSON.stringify(next))
  }

  const connectedCount = useMemo(() => Object.values(connections).filter(Boolean).length, [connections])

  return (
    <PageShell
      main={
        <div className="space-y-3">
          <Card>
            <div className="p-4 flex items-center justify-between gap-3">
              <div>
                <div className="text-[18px] font-semibold">My Network</div>
                <div className="text-[13px] text-black/60">{connectedCount} connections (local demo)</div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  className="h-10 w-[260px] rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
                  placeholder="Search people"
                />
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-3 border-b border-black/10">
              <div className="text-[14px] font-semibold">People you may know</div>
            </div>
            <div className="p-3 grid grid-cols-2 gap-3">
              {people.isLoading ? <div className="text-sm text-black/60">Loading…</div> : null}
              {people.data?.items.map((u) => {
                const isConnected = !!connections[u.id]
                return (
                  <div key={u.id} className="border border-black/10 rounded-lg p-3 flex gap-3">
                    <img src={u.avatar_url} className="h-12 w-12 rounded-full object-cover" />
                    <div className="min-w-0 flex-1">
                      <div className="text-[14px] font-semibold truncate">
                        {u.first_name} {u.last_name}
                      </div>
                      <div className="text-[12px] text-black/60 truncate">{u.headline}</div>
                      <div className="text-[12px] text-black/50 truncate">{u.location}</div>
                      <button
                        onClick={() => save({ ...connections, [u.id]: !isConnected })}
                        className={`mt-2 h-9 px-4 rounded-full border text-[13px] font-semibold ${
                          isConnected ? 'border-black/20 hover:bg-black/5' : 'border-[#0a66c2] text-[#0a66c2] hover:bg-[#0a66c2]/5'
                        }`}
                      >
                        {isConnected ? 'Remove connection' : 'Connect'}
                      </button>
                    </div>
                  </div>
                )
              })}
              {people.data && people.data.items.length === 0 ? (
                <div className="text-sm text-black/60">No people found for “{q}”.</div>
              ) : null}
            </div>
          </Card>
        </div>
      }
    />
  )
}

