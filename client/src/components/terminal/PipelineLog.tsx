import styles from './PipelineLog.module.css'

export type StepStatus = 'pending' | 'running' | 'done' | 'error'

export interface PipelineStep {
  id: string
  label: string
  status: StepStatus
}

interface PipelineLogProps {
  steps: PipelineStep[]
}

const statusIcons: Record<StepStatus, string> = {
  done: '\u2713 done',
  running: '\u25CF running',
  pending: '\u25CB pending',
  error: '\u2717 error',
}

export const PipelineLog = ({ steps }: PipelineLogProps) => {
  return (
    <div className={styles.log} role="log" aria-label="Pipeline progress">
      {steps.map((step) => (
        <div key={step.id} className={styles.step}>
          <span className={styles.prompt}>&gt;</span>
          <span className={styles.label}>{step.label}</span>
          <span className={`${styles.status} ${styles[step.status]}`}>
            {statusIcons[step.status]}
          </span>
        </div>
      ))}
    </div>
  )
}
