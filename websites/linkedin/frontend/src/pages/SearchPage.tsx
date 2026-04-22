import { useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { PageShell } from '../components/PageShell'
import { apiFetch } from '../lib/api'
import { useAuth } from '../lib/auth'

type CompanyOut = { id: string; name: string; industry: string; size_label: string; logo_url: string }
type JobListItem = {
  id: string
  title: string
  location: string
  work_mode: 'onsite' | 'hybrid' | 'remote'
  promoted: boolean
  actively_recruiting: boolean
  posted_at: string
  company: CompanyOut
  viewer_saved: boolean
}
type JobSearchResponse = { total: number; items: JobListItem[] }

type PostSearchItem = {
  id: string
  author: { id: string; first_name: string; last_name: string; headline: string; location: string; avatar_url: string }
  body: string
  image_url: string
  created_at: string
}
type PostSearchResponse = { total: number; items: PostSearchItem[] }

type PeopleSearchItem = { id: string; first_name: string; last_name: string; headline: string; location: string; avatar_url: string }
type PeopleSearchResponse = { total: number; items: PeopleSearchItem[] }

function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white border border-black/10 rounded-lg overflow-hidden">{children}</div>
}

function Tabs({ active, onChange }: { active: string; onChange(next: string): void }) {
  const tabs = [
    ['Jobs', 'jobs'],
    ['People', 'people'],
    ['Posts', 'posts'],
    ['Groups', 'groups'],
    ['Courses', 'courses'],
    ['Events', 'events'],
    ['Products', 'products'],
    ['Companies', 'companies'],
    ['Services', 'services'],
  ] as const
  return (
    <div className="flex items-center gap-5 text-[14px] border-b border-black/10">
      {tabs.map(([label, val]) => (
        <button
          key={val}
          onClick={() => onChange(val)}
          className={`py-3 font-semibold ${active === val ? 'text-black border-b-2 border-black' : 'text-black/60 hover:text-black'}`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

function RightRail() {
  const [email, setEmail] = useState('')
  const [ok, setOk] = useState(false)
  return (
    <div className="space-y-2">
      <Card>
        <div className="p-3">
          <div className="text-[14px] font-semibold">Get the latest jobs and industry news</div>
          <div className="text-[12px] text-black/60 mt-1">Weekly updates and recommendations. You can unsubscribe anytime.</div>
          <div className="mt-3">
            <label className="block text-[12px] text-black/60 mb-1">Email</label>
            <input
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setOk(false)
              }}
              className="w-full h-10 rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
              placeholder="you@example.com"
            />
            <button
              onClick={() => {
                const v = email.trim()
                if (!v) return
                localStorage.setItem('linkedin_clone_search_subscribe_email', v)
                setOk(true)
              }}
              className="mt-2 w-full h-10 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182]"
            >
              Subscribe
            </button>
            {ok ? <div className="mt-2 text-[12px] text-green-700">Subscribed (saved locally).</div> : null}
          </div>
        </div>
      </Card>
    </div>
  )
}

function JobsSection({ q, token }: { q: string; token: string }) {
  const jobs = useQuery({
    queryKey: ['search', 'jobs', q],
    queryFn: () =>
      apiFetch<JobSearchResponse>(`/jobs/search?query=${encodeURIComponent(q)}&location=${encodeURIComponent('United States')}&limit=4`, {
        accessToken: token,
      }),
    enabled: !!q,
  })
  return (
    <Card>
      <div className="p-3 border-b border-black/10 flex items-center justify-between">
        <div className="text-[16px] font-semibold">Jobs</div>
        <Link to={`/jobs?query=${encodeURIComponent(q)}&location=${encodeURIComponent('United States')}`} className="text-[13px] text-[#0a66c2] font-semibold hover:underline">
          See all job results in United States
        </Link>
      </div>
      <div className="divide-y divide-black/10">
        {jobs.isLoading ? <div className="p-3 text-sm text-black/60">Loading…</div> : null}
        {jobs.data?.items.map((j) => (
          <div key={j.id} className="p-3 flex gap-3">
            <img src={j.company.logo_url} className="h-12 w-12 rounded object-cover border border-black/10" />
            <div className="min-w-0 flex-1">
              <div className="text-[14px] font-semibold text-[#0a66c2] truncate">{j.title}</div>
              <div className="text-[13px] text-black/70 truncate">{j.company.name}</div>
              <div className="text-[12px] text-black/60 truncate">{j.location}</div>
            </div>
            <Link
              to={`/jobs?job=${encodeURIComponent(j.id)}&query=${encodeURIComponent(q)}&location=${encodeURIComponent('United States')}`}
              className="h-9 px-4 rounded-full border border-black/20 text-[13px] font-semibold hover:bg-black/5 flex items-center"
            >
              View
            </Link>
          </div>
        ))}
      </div>
    </Card>
  )
}

function PostsSection({ q, token }: { q: string; token: string }) {
  const [follows, setFollows] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem('linkedin_clone_follows') || '{}') as Record<string, boolean>
    } catch {
      return {}
    }
  })
  const posts = useQuery({
    queryKey: ['search', 'posts', q],
    queryFn: () => apiFetch<PostSearchResponse>(`/search/posts?q=${encodeURIComponent(q)}&limit=3`, { accessToken: token }),
    enabled: !!q,
  })
  return (
    <Card>
      <div className="p-3 border-b border-black/10 flex items-center justify-between">
        <div className="text-[16px] font-semibold">Posts</div>
        <Link
          to={`/search?q=${encodeURIComponent(q)}&tab=posts`}
          className="text-[13px] text-[#0a66c2] font-semibold hover:underline"
        >
          See all posts
        </Link>
      </div>
      <div className="divide-y divide-black/10">
        {posts.isLoading ? <div className="p-3 text-sm text-black/60">Loading…</div> : null}
        {posts.data?.items.map((p) => (
          <div key={p.id} className="p-3">
            <div className="flex items-start gap-2">
              <img src={p.author.avatar_url} className="h-10 w-10 rounded-full object-cover" />
              <div className="min-w-0 flex-1">
                <div className="text-[13px] font-semibold truncate">
                  {p.author.first_name} {p.author.last_name}
                </div>
                <div className="text-[12px] text-black/60 truncate">{p.author.headline}</div>
              </div>
              <button
                onClick={() => {
                  const next = { ...follows, [p.author.id]: !follows[p.author.id] }
                  setFollows(next)
                  localStorage.setItem('linkedin_clone_follows', JSON.stringify(next))
                }}
                className={`h-8 px-3 rounded-full border text-[12px] font-semibold hover:bg-[#0a66c2]/5 ${
                  follows[p.author.id] ? 'border-black/20 text-black/70 hover:bg-black/5' : 'border-[#0a66c2] text-[#0a66c2]'
                }`}
              >
                {follows[p.author.id] ? 'Following' : 'Follow'}
              </button>
            </div>
            <div className="mt-2 text-[13px] text-black/80 line-clamp-3 whitespace-pre-wrap">{p.body}</div>
          </div>
        ))}
      </div>
    </Card>
  )
}

function PeopleResults({ q, token }: { q: string; token: string }) {
  const [connections, setConnections] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem('linkedin_clone_connections') || '{}') as Record<string, boolean>
    } catch {
      return {}
    }
  })
  const people = useQuery({
    queryKey: ['search', 'people', q],
    queryFn: () => apiFetch<PeopleSearchResponse>(`/search/people?q=${encodeURIComponent(q)}&limit=10`, { accessToken: token }),
    enabled: !!q,
  })
  return (
    <Card>
      <div className="p-3 border-b border-black/10">
        <div className="text-[16px] font-semibold">People</div>
      </div>
      <div className="divide-y divide-black/10">
        {people.isLoading ? <div className="p-3 text-sm text-black/60">Loading…</div> : null}
        {people.data?.items.map((u) => (
          <div key={u.id} className="p-3 flex items-center gap-3">
            <img src={u.avatar_url} className="h-12 w-12 rounded-full object-cover" />
            <div className="min-w-0 flex-1">
              <div className="text-[14px] font-semibold truncate">
                {u.first_name} {u.last_name}
              </div>
              <div className="text-[12px] text-black/60 truncate">{u.headline}</div>
              <div className="text-[12px] text-black/50 truncate">{u.location}</div>
            </div>
            <button
              onClick={() => {
                const next = { ...connections, [u.id]: !connections[u.id] }
                setConnections(next)
                localStorage.setItem('linkedin_clone_connections', JSON.stringify(next))
              }}
              className="h-9 px-4 rounded-full border border-black/20 text-[13px] font-semibold hover:bg-black/5"
            >
              {connections[u.id] ? 'Remove' : 'Connect'}
            </button>
          </div>
        ))}
        {people.data && people.data.items.length === 0 ? (
          <div className="p-3 text-sm text-black/60">No people found for “{q}”.</div>
        ) : null}
      </div>
    </Card>
  )
}

function FeedbackCard() {
  const [v, setV] = useState<'yes' | 'no' | null>(null)
  return (
    <Card>
      <div className="p-3 flex items-center justify-between">
        <div className="text-[14px] font-semibold">Are these results helpful?</div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setV('yes')}
            className={`h-9 px-4 rounded-full border text-[13px] font-semibold ${v === 'yes' ? 'border-[#0a66c2] text-[#0a66c2]' : 'border-black/20 hover:bg-black/5'}`}
          >
            Yes
          </button>
          <button
            onClick={() => setV('no')}
            className={`h-9 px-4 rounded-full border text-[13px] font-semibold ${v === 'no' ? 'border-[#0a66c2] text-[#0a66c2]' : 'border-black/20 hover:bg-black/5'}`}
          >
            No
          </button>
        </div>
      </div>
    </Card>
  )
}

export function SearchPage() {
  const { tokens } = useAuth()
  const token = tokens!.access_token

  const navigate = useNavigate()
  const [params] = useSearchParams()
  const q = (params.get('q') ?? '').trim()
  const tab = (params.get('tab') ?? 'all').toLowerCase()

  const changeTab = (next: string) => {
    const p = new URLSearchParams(params)
    if (next === 'all') p.delete('tab')
    else p.set('tab', next)
    navigate(`/search?${p.toString()}`)
  }

  const effectiveTab = useMemo(() => {
    if (!q) return 'all'
    if (['jobs', 'people', 'posts', 'groups', 'courses', 'events', 'products', 'companies', 'services'].includes(tab)) return tab
    return 'all'
  }, [q, tab])

  return (
    <PageShell
      right={<RightRail />}
      main={
        <div className="space-y-3">
          <Tabs active={effectiveTab === 'all' ? 'jobs' : effectiveTab} onChange={(v) => changeTab(v === 'jobs' ? 'all' : v)} />

          {!q ? (
            <Card>
              <div className="p-6 text-[14px] text-black/70">Type a query in the search box to see results.</div>
            </Card>
          ) : effectiveTab === 'all' ? (
            <>
              <JobsSection q={q} token={token} />
              <PostsSection q={q} token={token} />
              <FeedbackCard />
            </>
          ) : effectiveTab === 'jobs' ? (
            <JobsSection q={q} token={token} />
          ) : effectiveTab === 'posts' ? (
            <PostsSection q={q} token={token} />
          ) : effectiveTab === 'people' ? (
            <PeopleResults q={q} token={token} />
          ) : (
            <Card>
              <div className="p-6 text-[14px] text-black/70">
                No results available for this category yet. Try switching tabs or refine your query.
              </div>
            </Card>
          )}
        </div>
      }
    />
  )
}

