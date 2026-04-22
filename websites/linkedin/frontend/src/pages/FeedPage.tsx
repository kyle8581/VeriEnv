import { useMemo, useState } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'

import { PageShell } from '../components/PageShell'
import { apiFetch } from '../lib/api'
import { useAuth } from '../lib/auth'

type UserPublic = { id: string; first_name: string; last_name: string; headline: string; location: string; avatar_url: string }

type PostOut = {
  id: string
  author: UserPublic
  body: string
  image_url: string
  created_at: string
  reactions_count: number
  comments_count: number
  viewer_has_liked: boolean
}

type CommentOut = { id: string; author: UserPublic; body: string; created_at: string }

type FeedRes = { items: PostOut[]; next_cursor?: string | null }

// Generate a consistent avatar URL using UI Avatars API
function getAvatarUrl(firstName: string, lastName: string, size: number = 200): string {
  const name = `${firstName}+${lastName}`
  const colors = ['0A66C2', '057642', 'C37D16', 'B24020', '5C3D9F', '006097']
  const colorIndex = (firstName.charCodeAt(0) + lastName.charCodeAt(0)) % colors.length
  const bg = colors[colorIndex]
  return `https://ui-avatars.com/api/?name=${name}&size=${size}&background=${bg}&color=fff&bold=true&format=svg`
}

// Avatar component with fallback
function Avatar({ user, size = 48, className = '' }: { user: UserPublic | { first_name: string; last_name: string; avatar_url?: string }; size?: number; className?: string }) {
  const [imgError, setImgError] = useState(false)
  const fallbackUrl = getAvatarUrl(user.first_name, user.last_name, size * 2)
  const avatarUrl = user.avatar_url && !imgError ? user.avatar_url : fallbackUrl
  
  return (
    <img 
      src={avatarUrl}
      onError={() => setImgError(true)}
      className={`rounded-full object-cover bg-[#f3f2ef] ${className}`}
      style={{ width: size, height: size }}
      alt={`${user.first_name} ${user.last_name}`}
    />
  )
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="linkedin-card overflow-hidden">{children}</div>
}

function Modal({
  title,
  open,
  onClose,
  children,
}: {
  title: string
  open: boolean
  onClose(): void
  children: React.ReactNode
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-[70] bg-black/40 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-[640px] bg-white rounded-lg border border-black/10 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-black/10 flex items-center justify-between">
          <div className="text-[16px] font-semibold">{title}</div>
          <button onClick={onClose} className="h-8 w-8 rounded-full hover:bg-black/5">
            ×
          </button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  )
}

function LeftRail() {
  const { me } = useAuth()
  return (
    <div className="space-y-2">
      <Card>
        {/* Profile banner */}
        <div className="h-14 bg-gradient-to-r from-[#004182] to-[#0073b1] rounded-t-lg" />
        <div className="px-3 pb-3 -mt-6">
          <div className="flex items-center gap-3">
            {me ? (
              <Avatar user={{ first_name: me.first_name || 'U', last_name: me.last_name || '', avatar_url: me.avatar_url }} size={56} className="border-2 border-white shadow-sm" />
            ) : (
              <div className="h-14 w-14 rounded-full bg-[#e7e7e7] border-2 border-white" />
            )}
          </div>
          <div className="mt-2">
            <div className="text-[16px] font-semibold">Welcome, {me?.first_name || 'User'}!</div>
            <Link to="/work" className="text-[12px] text-[#0a66c2] hover:underline">
              Add a photo
            </Link>
          </div>
        </div>
        <div className="border-t border-black/10 px-3 py-3">
          <div className="flex items-center justify-between text-[12px]">
            <span className="text-black/60">Connections</span>
            <span className="text-[#0a66c2] font-semibold">36</span>
          </div>
          <div className="mt-1 text-[12px] font-semibold text-black/90 hover:underline cursor-pointer">
            Grow your network
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-3 text-[12px] space-y-3">
          <div className="flex items-center gap-2 text-black/80 hover:text-black cursor-pointer">
            <span className="text-[16px]">📋</span>
            <span className="font-medium">Recent</span>
          </div>
          <div className="flex items-center gap-2 text-black/80 hover:text-black cursor-pointer">
            <span className="text-[16px]">👥</span>
            <span className="font-medium">Groups</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-black/80 hover:text-black cursor-pointer">
              <span className="text-[16px]">📅</span>
              <span className="font-medium">Events</span>
            </div>
            <button className="h-6 w-6 rounded hover:bg-black/5 text-black/60 hover:text-black font-bold">
              +
            </button>
          </div>
          <Link to="/search?q=%23bioinformatics" className="flex items-center gap-2 text-[#0a66c2] hover:underline">
            <span className="text-[16px]">#</span>
            <span className="font-medium">Followed Hashtags</span>
          </Link>
        </div>
        <Link to="/network" className="block border-t border-black/10 p-3 text-[13px] font-semibold text-black/60 hover:bg-black/5 text-center">
          Discover more
        </Link>
      </Card>
    </div>
  )
}

function RightRail() {
  const [expanded, setExpanded] = useState(false)
  const stories = [
    { title: 'Tech CEO exits in surprise move', time: '2h ago', readers: '12,345' },
    { title: 'Labor market shifts in 2026', time: '3h ago', readers: '8,234' },
    { title: 'AI skills you should build now', time: '4h ago', readers: '15,678' },
    { title: 'Genomics funding rebounds', time: '5h ago', readers: '6,543' },
    { title: 'Remote work policies evolve', time: '6h ago', readers: '9,876' },
    { title: 'Bio startups raise new rounds', time: '7h ago', readers: '4,321' },
    { title: 'Workplace AI policies change', time: '8h ago', readers: '7,654' },
    { title: 'Hiring rebounds in healthcare', time: '9h ago', readers: '5,432' },
  ]
  const show = expanded ? stories : stories.slice(0, 5)

  return (
    <div className="space-y-2">
      <Card>
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-[16px] text-black/90">LinkedIn News</div>
            <button className="h-5 w-5 rounded-full bg-black/10 text-[10px] text-black/70 font-bold flex items-center justify-center hover:bg-black/20">
              i
            </button>
          </div>
          <div className="mt-2 text-[12px] text-black/60 font-medium">Top stories</div>
          <ul className="mt-3 space-y-3">
            {show.map((story, idx) => (
              <li key={idx} className="flex gap-2 cursor-pointer group">
                <span className="mt-2 h-2 w-2 rounded-full bg-black/70 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-[13px] font-semibold text-black/90 group-hover:text-[#0a66c2] leading-tight">{story.title}</div>
                  <div className="text-[12px] text-black/50 mt-0.5">{story.time} • {story.readers} readers</div>
                </div>
              </li>
            ))}
          </ul>
          <button 
            onClick={() => setExpanded((v) => !v)} 
            className="mt-4 text-[13px] font-semibold text-black/70 hover:text-black flex items-center gap-1"
          >
            {expanded ? 'Show less ↑' : 'Show more ↓'}
          </button>
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <div className="text-[13px] text-black/70 text-center">Jane, unlock more with Premium</div>
          <div className="mt-3 flex justify-center">
            <div className="relative">
              <div className="h-16 w-16 rounded-lg bg-gradient-to-br from-[#f8c77e] to-[#c37d16] flex items-center justify-center">
                <span className="text-[24px] font-bold text-white">in</span>
              </div>
              <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-[#f8c77e] flex items-center justify-center">
                <span className="text-[12px]">⭐</span>
              </div>
            </div>
          </div>
          <Link
            to="/premium"
            className="mt-4 flex justify-center items-center w-full rounded-full border-2 border-[#0a66c2] text-[#0a66c2] font-semibold text-[14px] py-2 hover:bg-[#0a66c2] hover:text-white transition-colors"
          >
            Try 1 month for $0
          </Link>
        </div>
      </Card>
      
      {/* Footer links */}
      <div className="px-2 text-[11px] text-black/50 leading-relaxed">
        <div className="flex flex-wrap gap-x-2 gap-y-1">
          <a href="#" className="hover:text-[#0a66c2] hover:underline">About</a>
          <a href="#" className="hover:text-[#0a66c2] hover:underline">Accessibility</a>
          <a href="#" className="hover:text-[#0a66c2] hover:underline">Help Center</a>
          <a href="#" className="hover:text-[#0a66c2] hover:underline">Privacy & Terms</a>
          <a href="#" className="hover:text-[#0a66c2] hover:underline">Ad Choices</a>
          <a href="#" className="hover:text-[#0a66c2] hover:underline">Advertising</a>
        </div>
        <div className="mt-2 flex items-center gap-1">
          <span className="font-bold text-[#0a66c2]">in</span>
          <span>LinkedIn Corporation © 2026</span>
        </div>
      </div>
    </div>
  )
}

const MSG_KEY = 'linkedin_clone_messages_v1'

function appendLocalMessage(recipientId: string, body: string) {
  const msg = { id: crypto.randomUUID(), at: new Date().toISOString(), fromMe: true, body }
  let store: Record<string, any[]> = {}
  try {
    store = JSON.parse(localStorage.getItem(MSG_KEY) || '{}') as Record<string, any[]>
  } catch {
    store = {}
  }
  const next = { ...store, [recipientId]: [...(store[recipientId] ?? []), msg] }
  localStorage.setItem(MSG_KEY, JSON.stringify(next))
}

function Composer({ onOpen }: { onOpen(kind: 'post' | 'photo' | 'video' | 'event' | 'article'): void }) {
  const { me } = useAuth()
  return (
    <Card>
      <div className="p-4">
        <div className="flex items-center gap-3">
          {me ? (
            <Avatar user={{ first_name: me.first_name || 'U', last_name: me.last_name || '', avatar_url: me.avatar_url }} size={48} />
          ) : (
            <div className="h-12 w-12 rounded-full bg-[#e7e7e7]" />
          )}
          <button
            onClick={() => onOpen('post')}
            className="flex-1 h-12 rounded-full border border-black/40 text-left px-4 text-[14px] text-black/60 hover:bg-black/5 transition-colors"
          >
            Start a post
          </button>
        </div>
        <div className="mt-3 flex items-center justify-around">
          {([
            ['📷', 'Photo', 'photo'],
            ['🎬', 'Video', 'video'],
            ['📅', 'Event', 'event'],
            ['📝', 'Write article', 'article'],
          ] as const).map(([icon, label, kind]) => (
            <button key={label} onClick={() => onOpen(kind)} className="flex items-center gap-2 px-4 py-2 rounded-md action-btn">
              <span className="text-[18px]">{icon}</span>
              <span className="text-[13px] font-semibold text-black/70">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </Card>
  )
}

function PostCard({
  post,
  token,
  onToggleLike,
  onRepost,
}: {
  post: PostOut
  token: string
  onToggleLike(): void
  onRepost(): void
}) {
  const qc = useQueryClient()
  const [commentsOpen, setCommentsOpen] = useState(false)
  const [sendOpen, setSendOpen] = useState(false)
  const [recipientQ, setRecipientQ] = useState('')
  const [recipientId, setRecipientId] = useState<string | null>(null)
  const [messageBody, setMessageBody] = useState('')

  const comments = useQuery({
    queryKey: ['feed', 'comments', post.id],
    queryFn: () => apiFetch<CommentOut[]>(`/feed/posts/${post.id}/comments`, { accessToken: token }),
    enabled: commentsOpen,
  })

  const addComment = useMutation({
    mutationFn: (body: string) =>
      apiFetch<CommentOut>(`/feed/posts/${post.id}/comments`, { method: 'POST', accessToken: token, body: JSON.stringify({ body }) }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['feed', 'comments', post.id] })
      await qc.invalidateQueries({ queryKey: ['feed'] })
    },
  })

  const people = useQuery({
    queryKey: ['feed', 'send', 'people', recipientQ],
    queryFn: () => apiFetch<{ total: number; items: UserPublic[] }>(`/search/people?q=${encodeURIComponent(recipientQ)}&limit=8`, { accessToken: token }),
    enabled: sendOpen && recipientQ.trim().length > 0,
  })

  const recipientLabel = useMemo(() => {
    if (!recipientId) return ''
    const found = people.data?.items?.find((p) => p.id === recipientId)
    return found ? `${found.first_name} ${found.last_name}` : ''
  }, [recipientId, people.data])

  // Format relative time
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m`
    if (diffHours < 24) return `${diffHours}h`
    if (diffDays < 7) return `${diffDays}d`
    return date.toLocaleDateString()
  }

  return (
    <Card>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <Avatar user={post.author} size={48} />
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="text-[14px] font-semibold text-black/90 hover:text-[#0a66c2] hover:underline cursor-pointer">
                  {post.author.first_name} {post.author.last_name}
                </div>
                <div className="text-[12px] text-black/60 truncate leading-tight">{post.author.headline}</div>
                <div className="text-[12px] text-black/50 flex items-center gap-1">
                  <span>{formatTime(post.created_at)}</span>
                  <span>•</span>
                  <span>🌐</span>
                </div>
              </div>
              <button className="p-2 rounded-full hover:bg-black/5 text-black/60">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="5" cy="12" r="2" />
                  <circle cx="12" cy="12" r="2" />
                  <circle cx="19" cy="12" r="2" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div className="mt-3 text-[14px] text-black/90 whitespace-pre-wrap leading-relaxed">{post.body}</div>
      </div>
      {post.image_url ? (
        <img src={post.image_url} className="w-full max-h-[520px] object-cover" alt="" />
      ) : null}
      
      {/* Reactions summary */}
      <div className="px-4 py-2 flex items-center justify-between text-[12px] text-black/60">
        <div className="flex items-center gap-1">
          <span className="flex -space-x-1">
            <span className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-[#0a66c2] text-white text-[8px]">👍</span>
            <span className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-[#df704d] text-white text-[8px]">❤️</span>
          </span>
          <span className="ml-1">{post.reactions_count.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setCommentsOpen(v => !v)} className="hover:text-[#0a66c2] hover:underline">
            {post.comments_count.toLocaleString()} comments
          </button>
        </div>
      </div>
      
      {/* Action buttons */}
      <div className="border-t border-black/10 mx-3 grid grid-cols-4 text-[13px] text-black/70">
        <button 
          onClick={onToggleLike} 
          className={`py-3 font-semibold flex items-center justify-center gap-2 action-btn rounded-md my-1 ${post.viewer_has_liked ? 'text-[#0a66c2]' : ''}`}
        >
          <span className="text-[18px]">{post.viewer_has_liked ? '👍' : '👍'}</span>
          <span className="hidden sm:inline">{post.viewer_has_liked ? 'Liked' : 'Like'}</span>
        </button>
        <button onClick={() => setCommentsOpen((v) => !v)} className="py-3 font-semibold flex items-center justify-center gap-2 action-btn rounded-md my-1">
          <span className="text-[18px]">💬</span>
          <span className="hidden sm:inline">Comment</span>
        </button>
        <button onClick={onRepost} className="py-3 font-semibold flex items-center justify-center gap-2 action-btn rounded-md my-1">
          <span className="text-[18px]">🔄</span>
          <span className="hidden sm:inline">Repost</span>
        </button>
        <button onClick={() => setSendOpen(true)} className="py-3 font-semibold flex items-center justify-center gap-2 action-btn rounded-md my-1">
          <span className="text-[18px]">📤</span>
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>

      {commentsOpen ? (
        <div className="border-t border-black/10 p-4 bg-[#f9fafb]">
          <div className="mt-2 space-y-3">
            {comments.isLoading ? (
              <div className="flex items-center gap-2 text-sm text-black/60">
                <div className="h-4 w-4 border-2 border-[#0a66c2] border-t-transparent rounded-full animate-spin" />
                Loading comments…
              </div>
            ) : null}
            {comments.data?.map((c) => (
              <div key={c.id} className="flex gap-2">
                <Avatar user={c.author} size={32} />
                <div className="min-w-0 flex-1 bg-[#f2f2f2] rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-semibold text-black/90 hover:text-[#0a66c2] hover:underline cursor-pointer">
                      {c.author.first_name} {c.author.last_name}
                    </span>
                    <span className="text-[11px] text-black/50">• {c.author.headline?.split('•')[0]?.trim()}</span>
                  </div>
                  <div className="text-[13px] text-black/90 whitespace-pre-wrap mt-0.5">{c.body}</div>
                </div>
              </div>
            ))}
            {comments.data && comments.data.length === 0 ? (
              <div className="text-sm text-black/60 text-center py-4">Be the first to comment.</div>
            ) : null}
          </div>
          <form
            className="mt-4 flex items-start gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget)
              const body = String(fd.get('body') ?? '').trim()
              if (!body) return
              addComment.mutate(body)
              e.currentTarget.reset()
            }}
          >
            <input
              name="body"
              className="flex-1 h-10 rounded-full border border-black/30 px-4 outline-none focus:ring-2 focus:ring-[#0a66c2]/30 bg-white text-[14px]"
              placeholder="Add a comment…"
            />
            <button className="h-10 px-5 rounded-full bg-[#0a66c2] text-white text-[14px] font-semibold hover:bg-[#004182] transition-colors">
              Post
            </button>
          </form>
        </div>
      ) : null}

      <Modal
        title="Send in a message"
        open={sendOpen}
        onClose={() => {
          setSendOpen(false)
          setRecipientQ('')
          setRecipientId(null)
          setMessageBody('')
        }}
      >
        <div className="p-4 space-y-3">
          <div className="grid grid-cols-[1fr_1fr] gap-2">
            <input
              value={recipientQ}
              onChange={(e) => setRecipientQ(e.target.value)}
              className="h-10 rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
              placeholder="Search recipients"
            />
            <input
              value={recipientLabel}
              readOnly
              className="h-10 rounded border border-black/10 px-3 bg-black/5 text-black/60"
              placeholder="Recipient"
            />
          </div>
          {people.data?.items?.length ? (
            <div className="max-h-[160px] overflow-auto border border-black/10 rounded">
              {people.data.items.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setRecipientId(p.id)}
                  className={`w-full text-left px-3 py-2 text-[13px] hover:bg-black/5 ${
                    recipientId === p.id ? 'bg-[#e8f3ff]' : ''
                  }`}
                >
                  {p.first_name} {p.last_name} — <span className="text-black/60">{p.headline}</span>
                </button>
              ))}
            </div>
          ) : recipientQ.trim().length ? (
            <div className="text-[13px] text-black/60">No matching people found.</div>
          ) : (
            <div className="text-[13px] text-black/60">Search for a person to send this post.</div>
          )}
          <textarea
            value={messageBody}
            onChange={(e) => setMessageBody(e.target.value)}
            className="w-full h-28 rounded border border-black/20 px-3 py-2 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
            placeholder="Write a message…"
          />
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={() => {
                if (!recipientId) return
                const body = (messageBody || '').trim()
                const payload = `${body ? body + '\n\n' : ''}${post.body}`
                appendLocalMessage(recipientId, payload)
                setSendOpen(false)
              }}
              disabled={!recipientId}
              className="h-10 px-5 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182] disabled:opacity-60 disabled:hover:bg-[#0a66c2]"
            >
              Send
            </button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}

export function FeedPage() {
  const navigate = useNavigate()
  const { tokens } = useAuth()
  const token = tokens!.access_token
  const qc = useQueryClient()

  const feed = useInfiniteQuery({
    queryKey: ['feed'],
    queryFn: ({ pageParam }) => {
      const cursor = pageParam ? `&cursor=${encodeURIComponent(String(pageParam))}` : ''
      return apiFetch<FeedRes>(`/feed?limit=10${cursor}`, { accessToken: token })
    },
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  })

  const items = useMemo(() => feed.data?.pages.flatMap((p) => p.items) ?? [], [feed.data])

  const like = useMutation({
    mutationFn: (postId: string) =>
      apiFetch<{ liked: boolean }>(`/feed/posts/${postId}/like`, { method: 'POST', accessToken: token }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['feed'] }),
  })

  const createPost = useMutation({
    mutationFn: (payload: { body: string; image_url?: string }) =>
      apiFetch<PostOut>('/feed/posts', { method: 'POST', accessToken: token, body: JSON.stringify(payload) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['feed'] }),
  })

  const [composerOpen, setComposerOpen] = useState(false)
  const [composerKind, setComposerKind] = useState<'post' | 'photo' | 'video' | 'event' | 'article'>('post')
  const [composerBody, setComposerBody] = useState('')
  const [composerImageUrl, setComposerImageUrl] = useState('')

  return (
    <PageShell
      left={<LeftRail />}
      right={<RightRail />}
      main={
        <div className="space-y-2">
          <Composer
            onOpen={(kind) => {
              setComposerKind(kind)
              setComposerOpen(true)
            }}
          />

          {feed.isLoading ? <div className="text-black/60 text-sm">Loading feed…</div> : null}

          {items.map((p) => (
            <PostCard
              key={p.id}
              post={p}
              token={token}
              onToggleLike={() => like.mutate(p.id)}
              onRepost={() => {
                createPost.mutate({
                  body: `Repost from ${p.author.first_name} ${p.author.last_name}:\n\n${p.body}`,
                  image_url: p.image_url || '',
                })
              }}
            />
          ))}

          <div className="py-6 text-center">
            {feed.hasNextPage ? (
              <button
                onClick={() => feed.fetchNextPage()}
                className="h-9 px-4 rounded-full border border-black/20 text-[13px] font-semibold hover:bg-black/5"
              >
                Show more feed updates
              </button>
            ) : (
              <div className="text-[12px] text-black/40">You’re all caught up.</div>
            )}
          </div>

          <div className="fixed bottom-4 right-4">
            <button
              onClick={() => navigate('/messaging')}
              className="h-10 px-4 rounded-full bg-white border border-black/10 shadow-sm text-[13px] font-semibold hover:bg-black/5 flex items-center gap-2"
            >
              Messaging
            </button>
          </div>

          <Modal
            title={composerKind === 'post' ? 'Create a post' : composerKind === 'photo' ? 'Share a photo' : composerKind === 'video' ? 'Share a video' : composerKind === 'event' ? 'Create an event post' : 'Write an article'}
            open={composerOpen}
            onClose={() => setComposerOpen(false)}
          >
            <div className="p-4 space-y-3">
              <textarea
                value={composerBody}
                onChange={(e) => setComposerBody(e.target.value)}
                className="w-full h-36 rounded border border-black/20 px-3 py-2 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
                placeholder="What do you want to talk about?"
              />
              <input
                value={composerImageUrl}
                onChange={(e) => setComposerImageUrl(e.target.value)}
                className="w-full h-10 rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
                placeholder="Optional image URL"
              />
              <div className="flex items-center justify-end gap-2">
                <button
                  onClick={() => setComposerOpen(false)}
                  className="h-10 px-4 rounded-full border border-black/20 font-semibold hover:bg-black/5"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    const body = composerBody.trim()
                    if (!body) return
                    createPost.mutate({ body, image_url: composerImageUrl.trim() })
                    setComposerBody('')
                    setComposerImageUrl('')
                    setComposerOpen(false)
                  }}
                  className="h-10 px-5 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182]"
                >
                  Post
                </button>
              </div>
            </div>
          </Modal>
        </div>
      }
    />
  )
}

