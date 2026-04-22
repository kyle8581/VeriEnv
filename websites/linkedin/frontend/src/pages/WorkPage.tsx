import { Link } from 'react-router-dom'

import { PageShell } from '../components/PageShell'

function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white border border-black/10 rounded-lg overflow-hidden">{children}</div>
}

export function WorkPage() {
  const items: Array<{ title: string; desc: string; to: string }> = [
    { title: 'Home', desc: 'Your feed', to: '/feed' },
    { title: 'Search', desc: 'Find people, posts, jobs', to: '/search?q=bioinformatician' },
    { title: 'Jobs', desc: 'Search and apply', to: '/jobs' },
    { title: 'My Network', desc: 'Discover and connect', to: '/network' },
    { title: 'Messaging', desc: 'Chat with people', to: '/messaging' },
    { title: 'Notifications', desc: 'View updates', to: '/notifications' },
    { title: 'Premium', desc: 'Upgrade your experience', to: '/premium' },
  ]

  return (
    <PageShell
      main={
        <div className="space-y-3">
          <Card>
            <div className="p-4">
              <div className="text-[18px] font-semibold">Work</div>
              <div className="text-[13px] text-black/60 mt-1">Quick access to key areas of the clone.</div>
            </div>
          </Card>
          <div className="grid grid-cols-2 gap-3">
            {items.map((it) => (
              <Link key={it.to} to={it.to} className="block">
                <Card>
                  <div className="p-4 hover:bg-black/5">
                    <div className="text-[14px] font-semibold text-black/80">{it.title}</div>
                    <div className="text-[12px] text-black/60 mt-1">{it.desc}</div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      }
    />
  )
}

