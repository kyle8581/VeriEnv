import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'

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

type JobOut = {
  id: string
  title: string
  location: string
  work_mode: 'onsite' | 'hybrid' | 'remote'
  employment_type: 'full_time' | 'part_time' | 'contract' | 'internship'
  experience_level: 'internship' | 'entry' | 'mid' | 'senior' | 'director' | 'executive'
  promoted: boolean
  actively_recruiting: boolean
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  skills: string[]
  description: string
  apply_url: string
  posted_at: string
  applicants_count: number
  company: CompanyOut
  viewer_saved: boolean
  viewer_applied: boolean
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white border border-black/10 rounded-lg overflow-hidden">{children}</div>
}

function Pill({ label, onClick }: { label: string; onClick(): void }) {
  return (
    <button onClick={onClick} className="h-9 px-4 rounded-full border border-black/20 text-[13px] font-semibold hover:bg-black/5">
      {label}
    </button>
  )
}

function fmtMoney(min: number | null, max: number | null, cur: string | null) {
  if (!min || !max || !cur) return ''
  const f = (n: number) => n.toLocaleString()
  return `${cur} ${f(min)}/yr - ${cur} ${f(max)}/yr`
}

function WorkModeModal({
  open,
  selected,
  onClose,
  onApply,
}: {
  open: boolean
  selected: Array<'onsite' | 'hybrid' | 'remote'>
  onClose(): void
  onApply(next: Array<'onsite' | 'hybrid' | 'remote'>): void
}) {
  const [local, setLocal] = useState(selected)

  useEffect(() => setLocal(selected), [selected, open])
  if (!open) return null

  const toggle = (m: 'onsite' | 'hybrid' | 'remote') =>
    setLocal((prev) => (prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]))

  return (
    <div className="fixed inset-0 z-[60] bg-black/40 flex items-center justify-center p-4">
      <div className="w-full max-w-[520px] bg-white rounded-lg border border-black/10 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-black/10">
          <div className="text-[16px] font-semibold">On-site/remote</div>
        </div>
        <div className="p-4 space-y-3 text-[14px]">
          {([
            ['onsite', 'On-site'],
            ['hybrid', 'Hybrid'],
            ['remote', 'Remote'],
          ] as const).map(([val, label]) => (
            <label key={val} className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={local.includes(val)}
                onChange={() => toggle(val)}
                className="h-4 w-4"
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
        <div className="p-4 border-t border-black/10 flex items-center justify-end gap-2">
          <button onClick={onClose} className="h-10 px-4 rounded-full border border-black/20 font-semibold hover:bg-black/5">
            Cancel
          </button>
          <button
            onClick={() => {
              onApply(local)
              onClose()
            }}
            className="h-10 px-4 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182]"
          >
            Show results
          </button>
        </div>
      </div>
    </div>
  )
}

export function JobsPage() {
  const { tokens } = useAuth()
  const token = tokens!.access_token
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [params] = useSearchParams()

  const initialQuery = params.get('query') ?? params.get('q') ?? 'bioinformatician jobs'
  const initialLocation = params.get('location') ?? 'United States'
  const jobFromUrl = params.get('job') ?? ''

  const [query, setQuery] = useState(initialQuery)
  const [location, setLocation] = useState(initialLocation)
  const [workModes, setWorkModes] = useState<Array<'onsite' | 'hybrid' | 'remote'>>([])
  const [openWorkMode, setOpenWorkMode] = useState(false)
  const [datePostedDays, setDatePostedDays] = useState<number | null>(null)
  const [experienceLevel, setExperienceLevel] = useState<
    JobOut['experience_level'] | ''
  >('')
  const [employmentType, setEmploymentType] = useState<JobOut['employment_type'] | ''>('')
  const [company, setCompany] = useState('')

  const [selectedJobId, setSelectedJobId] = useState<string>(jobFromUrl)

  useEffect(() => {
    if (jobFromUrl) setSelectedJobId(jobFromUrl)
  }, [jobFromUrl])

  const qs = useMemo(() => {
    const p = new URLSearchParams()
    if (query.trim()) p.set('query', query.trim())
    if (location.trim()) p.set('location', location.trim())
    for (const m of workModes) p.append('work_mode', m)
    if (employmentType) p.append('employment_type', employmentType)
    if (experienceLevel) p.append('experience_level', experienceLevel)
    if (datePostedDays) p.set('date_posted_days', String(datePostedDays))
    if (company.trim()) p.set('query', `${query.trim()} ${company.trim()}`.trim())
    p.set('limit', '12')
    p.set('offset', '0')
    return p.toString()
  }, [query, location, workModes, employmentType, experienceLevel, datePostedDays, company])

  const jobs = useQuery({
    queryKey: ['jobs', 'search', qs],
    queryFn: () => apiFetch<JobSearchResponse>(`/jobs/search?${qs}`, { accessToken: token }),
  })

  useEffect(() => {
    if (!selectedJobId && jobs.data?.items?.length) {
      setSelectedJobId(jobs.data.items[0].id)
    }
  }, [jobs.data, selectedJobId])

  const detail = useQuery({
    queryKey: ['jobs', 'detail', selectedJobId],
    queryFn: () => apiFetch<JobOut>(`/jobs/${encodeURIComponent(selectedJobId)}`, { accessToken: token }),
    enabled: !!selectedJobId,
  })

  const save = useMutation({
    mutationFn: async (job: JobOut | JobListItem) => {
      if ((job as any).viewer_saved) {
        return apiFetch<{ saved: boolean }>(`/jobs/${job.id}/save`, { method: 'DELETE', accessToken: token })
      }
      return apiFetch<{ saved: boolean }>(`/jobs/${job.id}/save`, { method: 'POST', accessToken: token })
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['jobs', 'search'] })
      await qc.invalidateQueries({ queryKey: ['jobs', 'detail'] })
    },
  })

  const apply = useMutation({
    mutationFn: (jobId: string) => apiFetch<{ applied: boolean }>(`/jobs/${jobId}/apply`, { method: 'POST', accessToken: token }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['jobs', 'detail'] })
    },
  })

  const alertToggle = useMutation({
    mutationFn: (enabled: boolean) =>
      apiFetch<{ enabled: boolean }>(
        `/jobs/alerts/toggle?query=${encodeURIComponent(query.trim())}&location=${encodeURIComponent(location.trim())}&enabled=${enabled ? 'true' : 'false'}`,
        { method: 'POST', accessToken: token },
      ),
  })
  const [alertEnabled, setAlertEnabled] = useState(false)

  return (
    <PageShell
      main={
        <div className="space-y-3">
          <Card>
            <div className="p-3">
              <div className="grid grid-cols-[1fr_1fr_auto] gap-2 items-center">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search jobs"
                  className="h-11 rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
                />
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Location"
                  className="h-11 rounded border border-black/20 px-3 outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
                />
                <button
                  onClick={() => {
                    const p = new URLSearchParams()
                    p.set('query', query)
                    p.set('location', location)
                    navigate(`/jobs?${p.toString()}`)
                  }}
                  className="h-11 px-5 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182]"
                >
                  Search
                </button>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <div className="h-9 px-4 rounded-full border border-black/20 text-[13px] font-semibold flex items-center">
                  <select
                    value={datePostedDays ?? ''}
                    onChange={(e) => setDatePostedDays(e.target.value ? Number(e.target.value) : null)}
                    className="bg-transparent outline-none"
                    aria-label="Date posted"
                  >
                    <option value="">Date posted (any)</option>
                    <option value="1">Past 24 hours</option>
                    <option value="7">Past week</option>
                    <option value="30">Past month</option>
                  </select>
                </div>
                <div className="h-9 px-4 rounded-full border border-black/20 text-[13px] font-semibold flex items-center">
                  <select
                    value={experienceLevel}
                    onChange={(e) => setExperienceLevel(e.target.value as any)}
                    className="bg-transparent outline-none"
                    aria-label="Experience level"
                  >
                    <option value="">Experience level</option>
                    <option value="internship">Internship</option>
                    <option value="entry">Entry</option>
                    <option value="mid">Mid</option>
                    <option value="senior">Senior</option>
                    <option value="director">Director</option>
                    <option value="executive">Executive</option>
                  </select>
                </div>
                <input
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="Company"
                  className="h-9 w-[180px] rounded-full border border-black/20 px-4 text-[13px] font-semibold outline-none focus:ring-2 focus:ring-[#0a66c2]/20"
                />
                <div className="h-9 px-4 rounded-full border border-black/20 text-[13px] font-semibold flex items-center">
                  <select
                    value={employmentType}
                    onChange={(e) => setEmploymentType(e.target.value as any)}
                    className="bg-transparent outline-none"
                    aria-label="Job type"
                  >
                    <option value="">Job type</option>
                    <option value="full_time">Full-time</option>
                    <option value="part_time">Part-time</option>
                    <option value="contract">Contract</option>
                    <option value="internship">Internship</option>
                  </select>
                </div>
                <Pill label="On-site/remote" onClick={() => setOpenWorkMode(true)} />
                <Pill
                  label="All filters"
                  onClick={() => {
                    setWorkModes([])
                    setDatePostedDays(null)
                    setExperienceLevel('')
                    setEmploymentType('')
                    setCompany('')
                  }}
                />
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-[380px_1fr] gap-6 items-start">
            <Card>
              <div className="p-3 border-b border-black/10">
                <div className="text-[16px] font-semibold">
                  {query.trim() || 'Jobs'} {location.trim() ? `in ${location.trim()}` : ''}
                </div>
                <div className="mt-1 text-[12px] text-black/60">
                  {jobs.data ? `${jobs.data.total.toLocaleString()} results` : '—'}
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <div className="text-[13px] font-semibold text-black/70">Set alert</div>
                  <button
                    onClick={async () => {
                      const next = !alertEnabled
                      setAlertEnabled(next)
                      await alertToggle.mutateAsync(next).catch(() => setAlertEnabled(!next))
                    }}
                    className={`w-11 h-6 rounded-full border ${alertEnabled ? 'bg-[#0a66c2] border-[#0a66c2]' : 'bg-white border-black/20'} relative`}
                    aria-label="Toggle job alert"
                  >
                    <span
                      className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 rounded-full bg-white shadow border border-black/10 transition-all ${
                        alertEnabled ? 'left-5' : 'left-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
              <div className="divide-y divide-black/10">
                {jobs.isLoading ? <div className="p-3 text-sm text-black/60">Loading jobs…</div> : null}
                {jobs.data?.items.map((j) => (
                  <button
                    key={j.id}
                    onClick={() => {
                      setSelectedJobId(j.id)
                      const p = new URLSearchParams()
                      if (query.trim()) p.set('query', query.trim())
                      if (location.trim()) p.set('location', location.trim())
                      p.set('job', j.id)
                      navigate(`/jobs?${p.toString()}`, { replace: true })
                    }}
                    className={`w-full text-left p-3 hover:bg-black/5 ${selectedJobId === j.id ? 'bg-[#e8f3ff]' : ''}`}
                  >
                    <div className="flex items-start gap-3">
                      <img src={j.company.logo_url} className="h-12 w-12 rounded border border-black/10 object-cover" />
                      <div className="min-w-0 flex-1">
                        <div className="text-[14px] font-semibold text-[#0a66c2] truncate">{j.title}</div>
                        <div className="text-[13px] text-black/70 truncate">{j.company.name}</div>
                        <div className="text-[12px] text-black/60 truncate">
                          {j.location} • {j.work_mode === 'onsite' ? 'On-site' : j.work_mode === 'hybrid' ? 'Hybrid' : 'Remote'}
                        </div>
                        {j.promoted ? <div className="text-[12px] text-black/50 mt-1">Promoted</div> : null}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          save.mutate(j)
                        }}
                        className="h-9 px-3 rounded-full border border-black/20 text-[12px] font-semibold hover:bg-black/5"
                      >
                        {j.viewer_saved ? 'Saved' : 'Save'}
                      </button>
                    </div>
                  </button>
                ))}
              </div>
            </Card>

            <Card>
              {detail.isLoading ? (
                <div className="p-6 text-sm text-black/60">Loading job…</div>
              ) : detail.data ? (
                <div className="p-5">
                  <div className="text-[22px] font-semibold">{detail.data.title}</div>
                  <div className="mt-1 text-[14px] text-black/70">
                    {detail.data.company.name} • {detail.data.location}{' '}
                    {detail.data.work_mode ? `• ${detail.data.work_mode === 'onsite' ? 'On-site' : detail.data.work_mode === 'hybrid' ? 'Hybrid' : 'Remote'}` : ''}
                  </div>
                  <div className="mt-1 text-[12px] text-black/60">
                    {new Date(detail.data.posted_at).toLocaleDateString()} • {detail.data.applicants_count.toLocaleString()} applicants
                  </div>

                  {fmtMoney(detail.data.salary_min, detail.data.salary_max, detail.data.salary_currency) ? (
                    <div className="mt-2 text-[13px] text-black/70">{fmtMoney(detail.data.salary_min, detail.data.salary_max, detail.data.salary_currency)}</div>
                  ) : null}

                  <div className="mt-2 text-[13px] text-black/70">
                    {detail.data.employment_type === 'full_time'
                      ? 'Full-time'
                      : detail.data.employment_type === 'part_time'
                        ? 'Part-time'
                        : detail.data.employment_type === 'contract'
                          ? 'Contract'
                          : 'Internship'}{' '}
                    • {detail.data.company.size_label}
                  </div>

                  {detail.data.skills?.length ? (
                    <div className="mt-2 text-[13px] text-black/70">
                      Skills: <span className="font-semibold text-black/70">{detail.data.skills.slice(0, 3).join(', ')}</span>
                      {detail.data.skills.length > 3 ? `, +${detail.data.skills.length - 3} more` : ''}
                    </div>
                  ) : null}

                  <div className="mt-4 flex items-center gap-2">
                    <button
                      onClick={() => apply.mutate(detail.data!.id)}
                      disabled={detail.data.viewer_applied}
                      className="h-10 px-6 rounded-full bg-[#0a66c2] text-white font-semibold hover:bg-[#004182] disabled:opacity-60 disabled:hover:bg-[#0a66c2]"
                    >
                      {detail.data.viewer_applied ? 'Applied' : 'Apply'}
                    </button>
                    <button
                      onClick={() => save.mutate(detail.data!)}
                      className="h-10 px-6 rounded-full border border-black/20 font-semibold hover:bg-black/5"
                    >
                      {detail.data.viewer_saved ? 'Saved' : 'Save'}
                    </button>
                    <a
                      href={detail.data.apply_url}
                      target="_blank"
                      rel="noreferrer"
                      className="h-10 px-5 rounded-full border border-black/20 font-semibold hover:bg-black/5 flex items-center"
                    >
                      External apply
                    </a>
                  </div>

                  <div className="mt-6">
                    <div className="text-[16px] font-semibold">About the job</div>
                    <div className="mt-2 text-[14px] whitespace-pre-wrap text-black/80 leading-6">{detail.data.description}</div>
                  </div>
                </div>
              ) : (
                <div className="p-6 text-sm text-black/60">Select a job to see details.</div>
              )}
            </Card>
          </div>

          <WorkModeModal
            open={openWorkMode}
            selected={workModes}
            onClose={() => setOpenWorkMode(false)}
            onApply={(next) => setWorkModes(next)}
          />
        </div>
      }
    />
  )
}

