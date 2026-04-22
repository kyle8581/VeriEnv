import { useMemo, useState } from 'react'

import { PageShell } from '../components/PageShell'

function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white border border-black/10 rounded-lg overflow-hidden">{children}</div>
}

const KEY = 'linkedin_clone_premium_trial_started_at'

export function PremiumPage() {
  const [startedAt, setStartedAt] = useState<string | null>(() => localStorage.getItem(KEY))
  const started = useMemo(() => (startedAt ? new Date(startedAt) : null), [startedAt])

  return (
    <PageShell
      main={
        <div className="space-y-3">
          <Card>
            <div className="p-5">
              <div className="text-[20px] font-semibold">Try Premium</div>
              <div className="text-[13px] text-black/60 mt-1">This is a clone feature page; trial state is stored locally.</div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-[13px] text-black/70">
                <div className="p-3 rounded bg-[#f3f2ef]">See who viewed your profile</div>
                <div className="p-3 rounded bg-[#f3f2ef]">Get job insights and salary ranges</div>
                <div className="p-3 rounded bg-[#f3f2ef]">InMail messaging credits (demo)</div>
                <div className="p-3 rounded bg-[#f3f2ef]">Premium badge (demo)</div>
              </div>

              {started ? (
                <div className="mt-4 p-3 rounded border border-green-200 bg-green-50 text-[13px] text-green-900">
                  Trial started on {started.toLocaleString()}.
                </div>
              ) : null}

              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => {
                    const v = new Date().toISOString()
                    localStorage.setItem(KEY, v)
                    setStartedAt(v)
                  }}
                  className="h-10 px-5 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182]"
                >
                  Start free trial
                </button>
                <button
                  onClick={() => {
                    localStorage.removeItem(KEY)
                    setStartedAt(null)
                  }}
                  className="h-10 px-5 rounded-full border border-black/20 font-semibold hover:bg-black/5"
                >
                  Reset trial
                </button>
              </div>
            </div>
          </Card>
        </div>
      }
    />
  )
}

