import { ScreenerReportData } from '../types/resume'
import styles from './ScreenerReport.module.css'

interface ScreenerReportProps {
  report: ScreenerReportData
}

export function ScreenerReport({ report }: ScreenerReportProps) {
  const { screenerAnalysis, refinementChanges } = report

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>ATS Analysis & Refinement</h3>

      {/* Screener Analysis */}
      <section className={styles.section}>
        <h4 className={styles.sectionTitle}>ATS Screener Analysis</h4>
        <div className={styles.content}>
          <div className={styles.scoreSection}>
            <span className={styles.scoreLabel}>Overall Score:</span>
            <div className={styles.scoreBar}>
              <div className={styles.barContainer}>
                <div
                  className={`${styles.barFill} ${styles.barFillGreen}`}
                  style={{
                    width: `${screenerAnalysis.overallScore * 100}%`,
                  }}
                />
              </div>
              <span className={styles.scoreValue}>
                {(screenerAnalysis.overallScore * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {screenerAnalysis.terminologyMismatches.length > 0 && (
            <div>
              <span className={styles.listTitle}>Terminology Mismatches:</span>
              <ul className={styles.list}>
                {screenerAnalysis.terminologyMismatches.map((tm, i) => (
                  <li key={i} className={styles.listItem}>
                    <code className={`${styles.code} ${styles.codeMyTerm}`}>{tm.myTerm}</code>
                    {' → '}
                    <code className={`${styles.code} ${styles.codeJdTerm}`}>{tm.jdTerm}</code>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {screenerAnalysis.coverageGaps && screenerAnalysis.coverageGaps.length > 0 && (
            <div>
              <span className={styles.listTitle}>Coverage Gaps:</span>
              <ul className={styles.list}>
                {screenerAnalysis.coverageGaps.map((gap, i) => (
                  <li key={i} className={styles.listItem}>
                    <span
                      className={`${styles.badge} ${
                        gap.gapType === 'hard' ? styles.badgeHard : styles.badgeSoft
                      }`}
                    >
                      {gap.gapType.toUpperCase()}
                    </span>
                    <div className={styles.gapItem}>{gap.requirement}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>

      {/* Refinement Changes */}
      <section className={styles.section}>
        <h4 className={styles.sectionTitle}>Refinement Changes</h4>
        <div className={styles.content}>
          <div className={styles.scoreSection}>
            <span className={styles.scoreLabel}>Coverage Improvement:</span>
            <div className={styles.scoreBar}>
              <div className={styles.barContainer}>
                <div
                  className={`${styles.barFill} ${styles.barFillBlue}`}
                  style={{
                    width: `${refinementChanges.coverageImprovement * 100}%`,
                  }}
                />
              </div>
              <span className={styles.scoreValue}>
                +{(refinementChanges.coverageImprovement * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {refinementChanges.changes.length > 0 && (
            <div>
              <span className={styles.listTitle}>Changes Made:</span>
              <ul className={styles.list}>
                {refinementChanges.changes.map((change, i) => (
                  <li key={i} className={styles.changeItem}>
                    <span className={styles.changeSection}>{change.section}</span>:{' '}
                    {change.changeDescription}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {refinementChanges.remainingGaps.length > 0 && (
            <div>
              <span className={styles.listTitle}>Authentic Gaps (Unfixable):</span>
              <ul className={styles.list}>
                {refinementChanges.remainingGaps.map((gap, i) => (
                  <li key={i} className={styles.remainingGapItem}>
                    <div className={styles.remainingGapTitle}>{gap.requirement}</div>
                    <div className={styles.remainingGapDescription}>{gap.whyUnfixable}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
