import './ApiHint.css'

/**
 * Small icon that shows which backend endpoint a control uses.
 * @param {{ method: string, path: string, note?: string }} props
 */
export default function ApiHint({ method, path, note }) {
  const label = `${method.toUpperCase()} ${path}${note ? `\n${note}` : ''}`
  return (
    <span className="api-hint" title={label} aria-label={label} role="img">
      <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.2a.9.9 0 1 1 0 1.8.9.9 0 0 1 0-1.8zM6.9 7.1h2.2v4.5H6.9V7.1z" />
      </svg>
    </span>
  )
}
