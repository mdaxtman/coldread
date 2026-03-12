import type { TextareaHTMLAttributes } from 'react'
import styles from './TextArea.module.css'

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  showCharCount?: boolean
}

export const TextArea = ({
  showCharCount = false,
  value,
  className,
  ...props
}: TextAreaProps) => {
  const length = typeof value === 'string' ? value.length : 0

  return (
    <div className={styles.wrapper}>
      <textarea
        className={`${styles.textarea} ${className ?? ''}`}
        value={value}
        {...props}
      />
      {showCharCount && (
        <span className={styles.charCount}>{length.toLocaleString()} chars</span>
      )}
    </div>
  )
}
