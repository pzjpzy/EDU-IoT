const STEPS = ['Pre-Quiz', 'Challenges', 'Report', 'Post-Quiz']

export default function StepperNav({ current }: { current: number }) {
  return (
    <ol className="flex flex-wrap items-center gap-2 text-sm">
      {STEPS.map((label, i) => {
        const state = i < current ? 'done' : i === current ? 'active' : 'todo'
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={
                'flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold ' +
                (state === 'done'
                  ? 'border-emerald-500 bg-emerald-500/20 text-emerald-300'
                  : state === 'active'
                    ? 'border-sky-500 bg-sky-500/20 text-sky-300'
                    : 'border-slate-600 text-slate-500')
              }
            >
              {i + 1}
            </span>
            <span className={state === 'active' ? 'text-slate-100 font-medium' : 'text-slate-500'}>{label}</span>
            {i < STEPS.length - 1 && <span className="mx-1 text-slate-700">&rarr;</span>}
          </li>
        )
      })}
    </ol>
  )
}
