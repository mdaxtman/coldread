import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import type { FitReport, ResumeVariant } from '../../types'
import { MatchesList } from './MatchesList'
import { GapsList } from './GapsList'
import { TerminologyTable } from './TerminologyTable'
import styles from './FitReportView.module.css'

// Note: AnnotatedJd was moved into this feature alongside the other leaf
// components per the task's move instructions, but it isn't wired in here —
// it needs the raw JD text plus a keyword-coverage map, and neither is part
// of this view's prop contract (jdId is an identifier only; FitReport carries
// no keywordCoverage field). Fetching the JD independently here would also
// break this component's "no query client required" test setup.

interface FitReportViewProps {
  jdId: string
  fitReport: FitReport
  resume: ResumeVariant | null
  onGenerate: () => void
}

export const FitReportView = ({ jdId, fitReport, resume, onGenerate }: FitReportViewProps) => {
  const hardGaps = fitReport.gaps.filter((g) => g.type === 'hard').length
  const softGaps = fitReport.gaps.length - hardGaps
  const blocked = hardGaps > 0 || fitReport.fitLevel === 'poor'
  const score = fitReport.overallScore != null ? Math.round(fitReport.overallScore * 100) : null
  const gateVisible = resume === null && blocked
  // Once a resume exists, the gate copy is gone — surface the hard-gap count
  // in the chip row instead so it isn't lost entirely.
  const showHardGapsChip = hardGaps > 0 && !gateVisible

  return (
    <div className={styles.report} data-jd-id={jdId}>
      <section className={styles.hero}>
        <div className={styles.score} data-level={fitReport.fitLevel}>
          {score ?? '—'}
        </div>
        <div className={styles.heroBody}>
          <div className={styles.chips}>
            <Badge level={fitReport.fitLevel} />
            <span className={styles.chip}>{fitReport.matches.length} matches</span>
            <span className={styles.chip}>
              {softGaps} soft gap{softGaps === 1 ? '' : 's'}
            </span>
            {showHardGapsChip && (
              <span className={styles.chipDanger}>
                {hardGaps} hard gap{hardGaps === 1 ? '' : 's'}
              </span>
            )}
          </div>
          <p className={styles.reasoning}>{fitReport.reasoning}</p>
        </div>
      </section>

      {gateVisible && (
        <section className={styles.gate}>
          <p className={styles.gateTitle}>
            {hardGaps > 0
              ? `${hardGaps} hard gap${hardGaps === 1 ? '' : 's'} — resume generation can't close ${
                  hardGaps === 1 ? 'this' : 'these'
                } without fabrication.`
              : 'Fit is rated poor — resume generation is unlikely to produce a compelling result.'}
          </p>
          <p className={styles.gateHint}>The honest move is usually to pass. Your call:</p>
          <Button variant="secondary" onClick={onGenerate}>
            Generate anyway
          </Button>
        </section>
      )}

      {resume === null && !blocked && (
        <section className={styles.cta}>
          <div>
            <p className={styles.ctaTitle}>Generate a resume tailored to this role</p>
            <p className={styles.ctaMeta}>generate → screen → refine · 3 model calls</p>
          </div>
          <Button onClick={onGenerate}>Generate resume</Button>
        </section>
      )}

      <div className={styles.columns}>
        <MatchesList matches={fitReport.matches} />
        <GapsList gaps={fitReport.gaps} />
      </div>

      {fitReport.terminology.length > 0 && <TerminologyTable terminology={fitReport.terminology} />}

      {fitReport.culturalSignals.length > 0 && (
        <section className={styles.panel}>
          <h3 className={styles.panelTitle}>Cultural signals</h3>
          {fitReport.culturalSignals.map((s) => (
            <div key={s.quality} className={styles.signal}>
              <span className={styles.signalQuality}>{s.quality}</span>
              <span className={styles.signalJd}>&ldquo;{s.jdSignal}&rdquo;</span>
              <span className={styles.signalHint}>{s.evidenceHint}</span>
            </div>
          ))}
        </section>
      )}

      {fitReport.productConnection && (
        <section className={styles.connection}>
          <span className={styles.eyebrow}>Product connection</span>
          <p>{fitReport.productConnection}</p>
        </section>
      )}
    </div>
  )
}
