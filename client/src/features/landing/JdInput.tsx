import { TextArea } from '../../components/ui/TextArea'
import styles from './JdInput.module.css'

interface JdInputProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function JdInput({ value, onChange, disabled }: JdInputProps) {
  return (
    <div className={styles.wrapper}>
      <label htmlFor="jd-input" className={styles.label}>Paste a job description</label>
      <TextArea
        id="jd-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste the full job description here..."
        showCharCount
        disabled={disabled}
      />
    </div>
  )
}
