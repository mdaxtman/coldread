import styles from './CodeBlock.module.css'

interface CodeBlockProps {
  children: string
}

export function CodeBlock({ children }: CodeBlockProps) {
  return (
    <pre className={styles.block}>
      <code>{children}</code>
    </pre>
  )
}
