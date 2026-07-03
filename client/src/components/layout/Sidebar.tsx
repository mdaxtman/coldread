import { Link } from '@tanstack/react-router'
import { useUsageSummary } from '../../hooks/useRuns'
import styles from './Sidebar.module.css'

const NAV = [
  { to: '/', label: 'Analyze' },
  { to: '/runs', label: 'Runs' },
  { to: '/prompts', label: 'Prompts' },
] as const

export const Sidebar = () => {
  const usage = useUsageSummary()
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
            className={styles.navLink}
            activeProps={{ className: `${styles.navLink} ${styles.navLinkActive}` }}
            activeOptions={{ exact: item.to === '/' }}
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
            <span>this month</span>
            <span className={styles.usageValue}>
              ${usage.data.estCostUsd.toFixed(2)} · {usage.data.runCount} runs
            </span>
          </div>
        )}
      </footer>
    </aside>
  )
}
