import { PipelineLog } from '../../components/terminal/PipelineLog'
import type { PipelineStep } from '../../components/terminal/PipelineLog'
import styles from './PipelineProgress.module.css'

interface PipelineProgressProps {
  steps: PipelineStep[]
}

export function PipelineProgress({ steps }: PipelineProgressProps) {
  return (
    <div className={styles.wrapper}>
      <p className={styles.heading}>pipeline</p>
      <PipelineLog steps={steps} />
    </div>
  )
}
