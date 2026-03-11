import { Link, useRouterState } from '@tanstack/react-router'
import styles from './NavBar.module.css'

const navLinks = [
  { to: '/' as const, label: 'Home' },
  { to: '/results' as const, label: 'Results' },
] as const

export function NavBar() {
  const { location } = useRouterState()

  return (
    <nav className={styles.nav}>
      <Link to="/" className={styles.logo}>
        cold<span className={styles.logoAccent}>read</span>
      </Link>
      <ul className={styles.links}>
        {navLinks.map(({ to, label }) => (
          <li key={to}>
            <Link
              to={to}
              className={`${styles.link} ${
                to === '/'
                  ? location.pathname === '/'
                    ? styles.linkActive
                    : ''
                  : location.pathname.startsWith(to)
                    ? styles.linkActive
                    : ''
              }`}
            >
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
