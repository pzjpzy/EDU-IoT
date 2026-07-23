import { useNavigate } from 'react-router-dom'

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center px-6 py-12">
      <h1 className="mb-2 text-3xl font-bold text-slate-100">EduVAPT-IoT</h1>
      <p className="mb-8 text-slate-400">
        A guided, Hack The Box-style lab for learning IoT/CCTV network security. You do the hacking yourself with
        your own tools (Nmap, a browser, a Telnet client) against a live simulated camera - this platform just
        guides you step by step and tracks your progress.
      </p>

      <div className="rounded-lg border border-amber-600/40 bg-amber-500/10 p-5 text-sm text-slate-200 space-y-2">
        <p className="font-semibold text-amber-300">Authorised lab use only</p>
        <p>
          Only ever point a session at a target you own or are explicitly authorised to test - such as the bundled
          simulated camera container or a GNS3 lab topology you control.
        </p>
        <p>
          Sessions can only be created against private/loopback network ranges (configurable by an educator via{' '}
          <code className="rounded bg-slate-800 px-1">EDUVAPT_LAB_CIDRS</code>).
        </p>
      </div>

      <button
        onClick={() => navigate('/dashboard')}
        className="mt-8 self-start rounded-md bg-sky-600 px-5 py-2.5 font-medium text-white hover:bg-sky-500"
      >
        I understand - continue
      </button>
    </div>
  )
}
