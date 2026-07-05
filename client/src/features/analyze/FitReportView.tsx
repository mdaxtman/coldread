import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import type { FitReport, JobDescription, ResumeVariant } from '../../types'
import { AnnotatedJd } from './AnnotatedJd'
import { MatchesList } from './MatchesList'
import { GapsList } from './GapsList'
import { TerminologyTable } from './TerminologyTable'
import styles from './FitReportView.module.css'

interface FitReportViewProps {
  jdId: string
  fitReport: FitReport
  resume: ResumeVariant | null
  onGenerate: () => void
  // Optional so the frozen 4-prop contract (and existing callers/tests) keep
  // working; when provided, the annotated JD rail renders (design spec §4).
  jobDescription?: JobDescription | null
}

// Signal qualities arrive as machine keys/lowercase phrases; render them as a
// sentence, not Title Case Every Word.
const formatSignalQuality = (quality: string): string => {
  const plain = quality.replace(/_/g, ' ').toLowerCase()
  return plain.charAt(0).toUpperCase() + plain.slice(1)
}

export const FitReportView = ({
  jdId,
  fitReport,
  resume,
  onGenerate,
  jobDescription,
}: FitReportViewProps) => {
  const hardGaps = fitReport.gaps.filter((g) => g.type === 'hard').length
  const softGaps = fitReport.gaps.length - hardGaps
  const blocked = hardGaps > 0 || fitReport.fitLevel === 'poor'
  const score = fitReport.overallScore != null ? Math.round(fitReport.overallScore * 100) : null
  const gateVisible = resume === null && blocked

  // Screener coverage (post-generation) is richer; before a resume exists,
  // annotate the JD from the fit report itself so the section earns its name.
  const screenerCoverage = resume?.screenerReport.screenerAnalysis.keywordCoverage
  const fitCoverage: Record<string, boolean> = {}
  for (const gap of fitReport.gaps) fitCoverage[gap.requirement] = false
  for (const match of fitReport.matches) fitCoverage[match.requirement] = true
  for (const term of fitReport.terminology) fitCoverage[term.jdTerm] = true
  const coverage =
    screenerCoverage && Object.keys(screenerCoverage).length > 0 ? screenerCoverage : fitCoverage

  return (
    <div className={styles.report} data-jd-id={jdId}>
      <section className={styles.hero}>
        <div
          className={styles.scoreRing}
          data-level={fitReport.fitLevel}
          style={{ '--score-pct': `${score ?? 0}%` } as React.CSSProperties}
        >
          <div className={styles.score}>{score ?? '—'}</div>
          <span className={styles.scoreScale}>/ 100</span>
        </div>
        <div className={styles.heroBody}>
          <div className={styles.chips}>
            <Badge level={fitReport.fitLevel} />
            <span className={styles.chip}>{fitReport.matches.length} matches</span>
            {softGaps > 0 && (
              <span className={styles.chip}>
                {softGaps} soft gap{softGaps === 1 ? '' : 's'}
              </span>
            )}
            {hardGaps > 0 && (
              <span className={styles.chipDanger}>
                {hardGaps} hard gap{hardGaps === 1 ? '' : 's'}
              </span>
            )}
            {gateVisible && <span className={styles.chipDanger}>recommend: pass</span>}
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

      {jobDescription && (
        <section className={styles.panel}>
          <h3 className={styles.panelTitle}>Annotated JD</h3>
          <AnnotatedJd content={jobDescription.content} keywordCoverage={coverage} />
        </section>
      )}

      {fitReport.culturalSignals.length > 0 && (
        <section className={styles.panel}>
          <h3 className={styles.panelTitle}>Cultural signals</h3>
          {fitReport.culturalSignals.map((s) => (
            <div key={s.quality} className={styles.signal}>
              <span className={styles.signalQuality}>{formatSignalQuality(s.quality)}</span>
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
