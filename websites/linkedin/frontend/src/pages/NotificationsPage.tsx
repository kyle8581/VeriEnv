import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { PageShell } from '../components/PageShell'
import { apiFetch } from '../lib/api'
import { useAuth } from '../lib/auth'

type PostOut = {
  id: string
  author: { id: string; first_name: string; last_name: string; headline: string; location: string; avatar_url: string }
  body: string
  image_url: string
  created_at: string
  reactions_count: number
  comments_count: number
  viewer_has_liked: boolean
}
type FeedRes = { items: PostOut[]; next_cursor?: string | null }

function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white border border-black/10 rounded-lg overflow-hidden">{children}</div>
}

const KEY = 'linkedin_clone_notification_reads'

export function NotificationsPage() {
  const { tokens } = useAuth()
  const token = tokens!.access_token

  const [reads, setReads] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || '{}') as Record<string, boolean>
    } catch {
      return {}
    }
  })

  const feed = useQuery({
    queryKey: ['notifications', 'feed'],
    queryFn: () => apiFetch<FeedRes>('/feed?limit=10', { accessToken: token }),
  })

  const items = useMemo(() => feed.data?.items ?? [], [feed.data])
  const unreadCount = useMemo(() => items.filter((p) => !reads[p.id]).length, [items, reads])

  const markRead = (id: string) => {
    const next = { ...reads, [id]: true }
    setReads(next)
    localStorage.setItem(KEY, JSON.stringify(next))
  }

  return (
    <PageShell
      main={
        <div className="space-y-3">
          <Card>
            <div className="p-4 flex items-center justify-between">
              <div>
                <div className="text-[18px] font-semibold">Notifications</div>
                <div className="text-[13px] text-black/60">{unreadCount} unread (local state)</div>
              </div>
              <button
                onClick={() => {
                  setReads({})
                  localStorage.removeItem(KEY)
                }}
                className="h-10 px-4 rounded-full border border-black/20 font-semibold hover:bg-black/5"
              >
                Reset read state
              </button>
            </div>
          </Card>

          <Card>
            <div className="divide-y divide-black/10">
              {feed.isLoading ? <div className="p-3 text-sm text-black/60">Loading…</div> : null}
              {items.map((p) => {
                const read = !!reads[p.id]
                return (
                  <button
                    key={p.id}
                    onClick={() => markRead(p.id)}
                    className={`w-full text-left p-3 hover:bg-black/5 ${read ? 'bg-white' : 'bg-[#fff6e6]'}`}
                  >
                    <div className="flex items-center gap-3">
                      <img src={p.author.avatar_url} className="h-12 w-12 rounded-full object-cover" />
                      <div className="min-w-0 flex-1">
                        <div className="text-[13px] text-black/80">
                          <span className="font-semibold">
                            {p.author.first_name} {p.author.last_name}
                          </span>{' '}
                          posted: <span className="text-black/70 line-clamp-1">{p.body}</span>
                        </div>
                        <div className="text-[12px] text-black/50">{new Date(p.created_at).toLocaleString()}</div>
                      </div>
                      {!read ? <span className="h-2.5 w-2.5 rounded-full bg-[#0a66c2]" /> : null}
                    </div>
                  </button>
                )
              })}
              {feed.data && items.length === 0 ? <div className="p-3 text-sm text-black/60">No notifications yet.</div> : null}
            </div>
          </Card>
        </div>
      }
    />
  )
}

