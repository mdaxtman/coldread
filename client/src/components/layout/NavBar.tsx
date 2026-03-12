import { Link, useRouterState } from '@tanstack/react-router'
import styles from './NavBar.module.css'

const navLinks = [
  { to: '/' as const, label: 'Home' },
  { to: '/results' as const, label: 'Results' },
] as const

export const NavBar = () => {
  const { location } = useRouterState()

  return (
    <nav className={styles.nav}>
      <Link to="/" className={styles.logo}>
        cold<span className={styles.logoAccent}>read</span>
      </Link>
      <ul className={styles.links}>
        {navLinks.map(({ to, label }) => {
          let isActive = location.pathname === '/'
          if (!isActive) {
            isActive = location.pathname.startsWith(to)
          }

          return (
            <li key={to}>
              <Link to={to} className={`${styles.link} ${isActive ? styles.linkActive : ''}`}>
                {label}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
