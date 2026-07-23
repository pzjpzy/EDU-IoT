import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { useEffect, useRef } from 'react'
import { terminalWsUrl } from '../api/client'

export default function TerminalPanel({ onClose }: { onClose: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const term = new Terminal({
      convertEol: true,
      fontSize: 13,
      fontFamily: 'ui-monospace, Consolas, monospace',
      theme: { background: '#0f1115' },
    })
    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(container)
    fitAddon.fit()

    const ws = new WebSocket(terminalWsUrl())

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }))
    }
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'output') {
        term.write(msg.data)
      } else if (msg.type === 'exit') {
        term.write('\r\n\r\n[shell exited]\r\n')
      }
    }
    ws.onerror = () => {
      term.write('\r\n[connection error - is the backend running?]\r\n')
    }

    const dataDisposable = term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'input', data }))
      }
    })

    const resizeObserver = new ResizeObserver(() => {
      fitAddon.fit()
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }))
      }
    })
    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
      dataDisposable.dispose()
      ws.close()
      term.dispose()
    }
  }, [])

  return (
    <div className="rounded-lg border border-slate-700 bg-[#0f1115] p-2">
      <div className="mb-2 flex items-center justify-between px-1">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Terminal - type nmap / telnet commands directly here
        </span>
        <button onClick={onClose} className="text-xs text-slate-500 hover:text-slate-300">
          Close
        </button>
      </div>
      <div ref={containerRef} style={{ height: '360px' }} />
    </div>
  )
}
