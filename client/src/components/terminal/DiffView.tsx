import styles from './DiffView.module.css'

export interface DiffLine {
  type: 'added' | 'removed' | 'unchanged'
  content: string
}

interface DiffViewProps {
  lines: DiffLine[]
  showLineNumbers?: boolean
}

export const DiffView = ({ lines, showLineNumbers = true }: DiffViewProps) => {
  return (
    <div className={styles.diff} role="region" aria-label="Diff view">
      {lines.map((line, i) => (
        <div key={i} className={`${styles.line} ${styles[line.type]}`}>
          {showLineNumbers && <span className={styles.lineNumber}>{i + 1}</span>}
          {line.type === 'added' && '+ '}
          {line.type === 'removed' && '- '}
          {line.type === 'unchanged' && '  '}
          {line.content}
        </div>
      ))}
    </div>
  )
}
