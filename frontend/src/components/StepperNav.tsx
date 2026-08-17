const STEPS = ['Pre-Quiz', 'Recon', 'Challenges', 'Report', 'Capstone', 'Summary']

interface Props {
  current: number
  /** Highest phase the student has reached; phases up to here are clickable. */
  furthest?: number
  onNavigate?: (step: number) => void
}

export default function StepperNav({ current, furthest = current, onNavigate }: Props) {
  return (
    <ol className="flex flex-wrap items-center gap-2 text-sm">
      {STEPS.map((label, i) => {
        const state = i < current ? 'done' : i === current ? 'active' : 'todo'
        const reachable = onNavigate != null && i <= furthest && i !== current
        return (
          <li key={label} className="flex items-center gap-2">
            <button
              type="button"
              disabled={!reachable}
              onClick={() => reachable && onNavigate?.(i)}
              title={reachable ? `Go to ${label}` : undefined}
              className={
                'flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold ' +
                (state === 'done'
                  ? 'border-emerald-500 bg-emerald-500/20 text-emerald-300'
                  : state === 'active'
                    ? 'border-sky-500 bg-sky-500/20 text-sky-300'
                    : 'border-slate-600 text-slate-500') +
                (reachable ? ' cursor-pointer hover:brightness-125' : ' cursor-default')
              }
            >
              {i + 1}
            </button>
            <button
              type="button"
              disabled={!reachable}
              onClick={() => reachable && onNavigate?.(i)}
              className={
                (state === 'active' ? 'text-slate-100 font-medium' : 'text-slate-500') +
                (reachable ? ' cursor-pointer hover:text-slate-300' : ' cursor-default')
              }
            >
              {label}
            </button>
            {i < STEPS.length - 1 && <span className="mx-1 text-slate-700">&rarr;</span>}
          </li>
        )
      })}
    </ol>
  )
}
