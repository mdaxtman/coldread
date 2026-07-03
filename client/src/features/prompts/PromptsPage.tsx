import { usePrompts } from '../../hooks/useRuns'
import { Card } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import styles from './PromptsPage.module.css'

export const PromptsPage = () => {
  const prompts = usePrompts()
  const active = prompts.data?.filter((p) => p.active) ?? []

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Observability</p>
        <h1>Prompts</h1>
      </header>

      {prompts.isLoading && <div className={styles.loading}>loading…</div>}
      {!prompts.isLoading && active.length === 0 && (
        <div className={styles.empty}>No active prompts.</div>
      )}

      <div className={styles.list}>
        {active.map((prompt) => (
          <Card key={prompt.id} className={styles.card}>
            <div className={styles.cardHeader}>
              <p className={styles.eyebrowSmall}>{prompt.stage}</p>
              <div className={styles.titleRow}>
                <h2 className={styles.name}>{prompt.name}</h2>
                <Badge level="machine" label={`v${prompt.version}`} />
              </div>
            </div>
            <pre className={styles.template}>{prompt.template}</pre>
          </Card>
        ))}
      </div>
    </div>
  )
}
