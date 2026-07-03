import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { createJobDescription } from '../../api/client'
import { useRuns } from '../../hooks/useRuns'
import { Button } from '../../components/ui/Button'
import { TextArea } from '../../components/ui/TextArea'
import styles from './AnalyzePage.module.css'

const MAX_CHARS = 50000

export const AnalyzePage = () => {
  const navigate = useNavigate()
  const { jd } = useSearch({ from: '/' })
  const [content, setContent] = useState('')
  const runs = useRuns()

  // ?jd= handoff from the portfolio: prefill as seed text, scrub the URL,
  // never auto-run (user reviews before spending API budget).
  useEffect(() => {
    if (jd) {
      setContent(jd)
      void navigate({ to: '/', search: {}, replace: true })
    }
  }, [jd, navigate])

  const create = useMutation({
    mutationFn: () => createJobDescription({ content }),
    onSuccess: (row) => navigate({ to: '/analyze/$jdId', params: { jdId: row.id } }),
  })

  return (
    <div className={styles.page}>
      <div className={styles.main}>
        <p className={styles.eyebrow}>Stage 1 · Fit assessment</p>
        <h1 className={styles.headline}>
          Screen the job <em>before</em> it screens you.
        </h1>
        <p className={styles.sub}>
          Paste a job description. The pipeline returns an honest fit report — matches, gaps,
          terminology drift — and shows you exactly what the model did to get there.
        </p>

        <div className={styles.inputPanel}>
          <TextArea
            value={content}
            onChange={(e) => setContent(e.target.value.slice(0, MAX_CHARS))}
            placeholder="Paste a job description…"
            rows={14}
            aria-label="Job description"
          />
          <div className={styles.inputMeta}>
            <span>
              {content.length.toLocaleString()} / {MAX_CHARS.toLocaleString()} chars
            </span>
            <span>≈ {Math.ceil(content.length / 4).toLocaleString()} tokens</span>
          </div>
        </div>

        <div className={styles.runRow}>
          <Button onClick={() => create.mutate()} disabled={!content.trim() || create.isPending}>
            {create.isPending ? 'Saving…' : 'Continue to analysis →'}
          </Button>
          {create.isError && (
            <span className={styles.error}>Could not save the JD — is the API running?</span>
          )}
        </div>
      </div>

      <aside className={styles.rail}>
        <p className={styles.eyebrow}>Recent runs</p>
        {(runs.data ?? []).slice(0, 5).map((r) => (
          <a key={r.id} href={`/runs/${r.id}`} className={styles.runCard}>
            <span className={styles.runTitle}>{r.jdTitle ?? 'Untitled JD'}</span>
            <span className={styles.runMeta}>
              {r.kind} · {r.status} · ${r.estCostUsd.toFixed(3)}
            </span>
          </a>
        ))}
      </aside>
    </div>
  )
}
