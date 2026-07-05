import { useState } from 'react'
import styles from './CodeBlock.module.css'

interface CodeBlockProps {
  children: string
  copyable?: boolean
}

export const CodeBlock = ({ children, copyable = false }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false)

  if (!copyable) {
    return (
      <pre className={styles.block}>
        <code>{children}</code>
      </pre>
    )
  }

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        className={styles.copy}
        onClick={() => {
          void navigator.clipboard.writeText(children)
          setCopied(true)
          setTimeout(() => setCopied(false), 1500)
        }}
      >
        {copied ? 'copied' : 'copy'}
      </button>
      <pre className={styles.block}>
        <code>{children}</code>
      </pre>
    </div>
  )
}
