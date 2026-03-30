import { Link, useParams } from '@tanstack/react-router'
import { Button } from '../../components/ui/Button'
import { SplitPanel } from '../../components/layout/SplitPanel'
import { ResumePanel } from './ResumePanel'
import { SupportingPanel } from './SupportingPanel'
import { useResultsData } from '../../hooks/useResultsData'
import styles from './ResultsDashboard.module.css'

export const ResultsDashboard = () => {
  const { jdId } = useParams({ from: '/results/$jdId' })
  const { data, isLoading, error } = useResultsData(jdId)

  if (isLoading) {
    return (
      <div className={styles.empty}>
        <p>Loading results…</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className={styles.empty}>
        <h2 className={styles.emptyHeading}>Failed to load results</h2>
        <p style={{ marginBottom: 'var(--space-6)' }}>
          {error?.message ?? 'Something went wrong.'}
        </p>
        <Link to="/">
          <Button>Go to Home</Button>
        </Link>
      </div>
    )
  }

  const { jobDescription, fitReport, resumeVariant } = data

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h1 className={styles.title}>Analysis Results</h1>
        <p className={styles.subtitle}>
          {jobDescription.title} at {jobDescription.company}
        </p>
      </div>

      <SplitPanel>
        <ResumePanel resumeVariant={resumeVariant} fitLevel={fitReport.fitLevel} />
        <SupportingPanel
          fitReport={fitReport}
          jobDescription={jobDescription}
          keywordCoverage={resumeVariant.screenerReport.screenerAnalysis.keywordCoverage}
        />
      </SplitPanel>
    </div>
  )
}
