import { Outlet } from '@tanstack/react-router'
import { NavBar } from './NavBar'
import styles from './AppShell.module.css'

export function AppShell() {
  return (
    <div className={styles.shell}>
      <NavBar />
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
