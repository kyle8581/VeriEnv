import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { PageShell } from '../components/PageShell'
import { apiFetch } from '../lib/api'
import { useAuth } from '../lib/auth'

type PeopleSearchItem = { id: string; first_name: string; last_name: string; headline: string; location: string; avatar_url: string }
type PeopleSearchResponse = { total: number; items: PeopleSearchItem[] }

type Message = { id: string; at: string; fromMe: boolean; body: string }

function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white border border-black/10 rounded-lg overflow-hidden">{children}</div>
}

const KEY = 'linkedin_clone_messages_v1'

function loadStore(): Record<string, Message[]> {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '{}') as Record<string, Message[]>
  } catch {
    return {}
  }
}

function saveStore(store: Record<string, Message[]>) {
  localStorage.setItem(KEY, JSON.stringify(store))
}

export function MessagingPage() {
  const { tokens } = useAuth()
  const token = tokens!.access_token

  const [peopleQ, setPeopleQ] = useState('jane')
  const people = useQuery({
    queryKey: ['messaging', 'people', peopleQ],
    queryFn: () => apiFetch<PeopleSearchResponse>(`/search/people?q=${encodeURIComponent(peopleQ)}&limit=12`, { accessToken: token }),
    enabled: peopleQ.trim().length > 0,
  })

  const [store, setStore] = useState<Record<string, Message[]>>(() => loadStore())
  const [activeId, setActiveId] = useState<string | null>(null)
  const [draft, setDraft] = useState('')

  const active = useMemo(() => {
    if (!activeId) return null
    return people.data?.items.find((p) => p.id === activeId) ?? null
  }, [activeId, people.data])

  const thread = activeId ? store[activeId] ?? [] : []

  const send = () => {
    if (!activeId) return
    const body = draft.trim()
    if (!body) return
    const nextMsg: Message = { id: crypto.randomUUID(), at: new Date().toISOString(), fromMe: true, body }
    const next = { ...store, [activeId]: [...(store[activeId] ?? []), nextMsg] }
    setStore(next)
    saveStore(next)
    setDraft('')
  }

  return (
    <PageShell
      main={
        <div className="space-y-3">
          <Card>
            <div className="p-4">
              <div className="text-[18px] font-semibold">Messaging</div>
              <div className="text-[13px] text-black/60 mt-1">This clone stores messages locally (no backend messaging API).</div>
            </div>
          </Card>

          <div className="grid grid-cols-[320px_1fr] gap-6 items-start">
            <Card>
              <div className="p-3 border-b border-black/10">
                <input
                  value={peopleQ}
                  onChange={(e) => setPeopleQ(e.target.value)}
                  className="w-full h-10 rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
                  placeholder="Search people"
                />
              </div>
              <div className="divide-y divide-black/10">
                {people.data?.items.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setActiveId(p.id)}
                    className={`w-full text-left p-3 hover:bg-black/5 ${activeId === p.id ? 'bg-[#e8f3ff]' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <img src={p.avatar_url} className="h-10 w-10 rounded-full object-cover" />
                      <div className="min-w-0 flex-1">
                        <div className="text-[13px] font-semibold truncate">
                          {p.first_name} {p.last_name}
                        </div>
                        <div className="text-[12px] text-black/60 truncate">{p.headline}</div>
                      </div>
                    </div>
                  </button>
                ))}
                {people.isLoading ? <div className="p-3 text-sm text-black/60">Loading…</div> : null}
                {people.data && people.data.items.length === 0 ? <div className="p-3 text-sm text-black/60">No people found.</div> : null}
              </div>
            </Card>

            <Card>
              <div className="p-3 border-b border-black/10">
                <div className="text-[14px] font-semibold">
                  {active ? `${active.first_name} ${active.last_name}` : 'Select a conversation'}
                </div>
              </div>
              <div className="p-3 h-[420px] overflow-auto space-y-2 bg-[#f9fafb]">
                {activeId && thread.length === 0 ? <div className="text-sm text-black/60">No messages yet. Say hello.</div> : null}
                {thread.map((m) => (
                  <div key={m.id} className={`flex ${m.fromMe ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[70%] rounded-lg px-3 py-2 text-[13px] ${m.fromMe ? 'bg-[#0a66c2] text-white' : 'bg-white border border-black/10'}`}>
                      <div className="whitespace-pre-wrap">{m.body}</div>
                      <div className={`mt-1 text-[10px] ${m.fromMe ? 'text-white/80' : 'text-black/50'}`}>{new Date(m.at).toLocaleString()}</div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-3 border-t border-black/10 flex items-center gap-2">
                <input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') send()
                  }}
                  disabled={!activeId}
                  className="flex-1 h-10 rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20 disabled:bg-black/5"
                  placeholder={activeId ? 'Write a message…' : 'Select a conversation to write'}
                />
                <button
                  onClick={send}
                  disabled={!activeId}
                  className="h-10 px-4 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182] disabled:opacity-60 disabled:hover:bg-[#0a66c2]"
                >
                  Send
                </button>
              </div>
            </Card>
          </div>
        </div>
      }
    />
  )
}

