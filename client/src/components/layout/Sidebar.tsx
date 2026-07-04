import { Link, useRouterState } from '@tanstack/react-router'
import { useUsageSummary } from '../../hooks/useRuns'
import styles from './Sidebar.module.css'

const NAV = [
  { to: '/', label: 'Analyze' },
  { to: '/runs', label: 'Runs' },
  { to: '/prompts', label: 'Prompts' },
] as const

// TanStack's activeProps can't mark "Analyze" active on /analyze/$jdId
// (its `to` is '/'), so compute active state from the pathname directly.
const isNavActive = (to: string, pathname: string): boolean => {
  if (to === '/') return pathname === '/' || pathname.startsWith('/analyze')
  return pathname === to || pathname.startsWith(`${to}/`)
}

export const Sidebar = () => {
  const usage = useUsageSummary()
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.glyph} aria-hidden>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path
              d="M2 3h6M2 7h10M2 11h4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </span>
        <span className={styles.wordmark}>coldread</span>
      </div>

      <div className={styles.eyebrow}>Workspace</div>
      <nav className={styles.nav}>
        {NAV.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={
              isNavActive(item.to, pathname)
                ? `${styles.navLink} ${styles.navLinkActive}`
                : styles.navLink
            }
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <footer className={styles.footer}>
        <div className={styles.statusRow}>
          <span className={styles.statusDot} aria-hidden />
          <span>api</span>
        </div>
        {usage.data && (
          <div className={styles.usage}>
            <span>all-time</span>
            <span className={styles.usageValue}>
              ${usage.data.estCostUsd.toFixed(2)} · {usage.data.runCount} runs
            </span>
          </div>
        )}
      </footer>
    </aside>
  )
}
