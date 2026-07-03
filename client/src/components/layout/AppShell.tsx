import { Outlet } from '@tanstack/react-router'
import { Sidebar } from './Sidebar'
import styles from './AppShell.module.css'

export const AppShell = () => (
  <div className={styles.shell}>
    <Sidebar />
    <main className={styles.main}>
      <Outlet />
    </main>
  </div>
)
