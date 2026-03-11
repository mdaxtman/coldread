import type { ReactNode } from 'react'
import styles from './Section.module.css'

interface SectionProps {
  heading?: string
  description?: string
  children: ReactNode
}

export function Section({ heading, description, children }: SectionProps) {
  return (
    <section className={styles.section}>
      {heading && <h2 className={styles.heading}>{heading}</h2>}
      {description && <p className={styles.description}>{description}</p>}
      {children}
    </section>
  )
}
