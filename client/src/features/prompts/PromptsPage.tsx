import { useState } from 'react'
import { usePrompts } from '../../hooks/useRuns'
import { Card } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import type { Prompt } from '../../types'
import styles from './PromptsPage.module.css'

/**
 * Prompt names in the DB carry a trailing changelog note in parens
 * ("Resume Generator v5 (cultural signals + product connection)").
 * Split it out: the parenthetical is release-notes metadata, not a name.
 */
const splitName = (name: string): { title: string; note: string | null } => {
  const match = /^(.*?)\s*\((.+)\)\s*$/.exec(name)
  if (!match) return { title: name, note: null }
  return { title: match[1], note: match[2] }
}

const PromptCard = ({ prompt }: { prompt: Prompt }) => {
  const [expanded, setExpanded] = useState(false)
  const { title, note } = splitName(prompt.name)
  return (
    <Card className={styles.card}>
      <div className={styles.cardHeader}>
        <p className={styles.eyebrowSmall}>{prompt.stage}</p>
        <div className={styles.titleRow}>
          <h2 className={styles.name}>{title}</h2>
          <Badge level="machine" label={`v${prompt.version}`} />
        </div>
        {note && (
          <p className={styles.note}>
            v{prompt.version} — {note}
          </p>
        )}
      </div>
      <div className={expanded ? styles.templateOpen : styles.templateClamped}>
        <pre className={styles.template}>{prompt.template}</pre>
        {!expanded && <div className={styles.fade} aria-hidden />}
      </div>
      <button type="button" className={styles.toggle} onClick={() => setExpanded((v) => !v)}>
        {expanded ? 'Collapse' : 'Show full prompt'}
      </button>
    </Card>
  )
}

export const PromptsPage = () => {
  const prompts = usePrompts()
  const active = prompts.data?.filter((p) => p.active) ?? []

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Configuration</p>
        <h1>Prompts</h1>
      </header>

      {prompts.isLoading && <div className={styles.loading}>Fetching prompts…</div>}
      {!prompts.isLoading && active.length === 0 && (
        <div className={styles.empty}>No active prompts.</div>
      )}

      <div className={styles.list}>
        {active.map((prompt) => (
          <PromptCard key={prompt.id} prompt={prompt} />
        ))}
      </div>
    </div>
  )
}
