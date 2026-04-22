import { Header } from './Header'

export function PageShell({
  left,
  main,
  right,
}: {
  left?: React.ReactNode
  main: React.ReactNode
  right?: React.ReactNode
}) {
  const hasLeft = !!left
  const hasRight = !!right
  const cols = hasLeft && hasRight ? 'grid-cols-[225px_1fr_300px]' : hasLeft ? 'grid-cols-[225px_1fr]' : hasRight ? 'grid-cols-[1fr_300px]' : 'grid-cols-1'
  return (
    <div className="min-h-full">
      <Header />
      <div className="mx-auto max-w-[1128px] px-3 pt-4">
        <div className={`grid ${cols} gap-6 items-start`}>
          {hasLeft ? <div>{left}</div> : null}
          <div className="min-w-0">{main}</div>
          {hasRight ? <div>{right}</div> : null}
        </div>
      </div>
    </div>
  )
}

