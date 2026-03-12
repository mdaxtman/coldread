import { Link } from '@tanstack/react-router'
import { Button } from '../../components/ui/Button'
import { SplitPanel } from '../../components/layout/SplitPanel'
import { ResumePanel } from './ResumePanel'
import { SupportingPanel } from './SupportingPanel'
import { usePipelineResult } from '../../hooks/usePipelineResult'
import styles from './ResultsDashboard.module.css'

export const ResultsDashboard = () => {
  const { result } = usePipelineResult()

  if (!result) {
    return (
      <div className={styles.empty}>
        <h2 className={styles.emptyHeading}>No results yet</h2>
        <p style={{ marginBottom: 'var(--space-6)' }}>
          Run an analysis from the landing page to see results here.
        </p>
        <Link to="/">
          <Button>Go to Home</Button>
        </Link>
      </div>
    )
  }

  const { jobDescription, fitReport, resumeVariant } = result

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
          keywordCoverage={resumeVariant.screenerReport.keywordCoverage}
        />
      </SplitPanel>
    </div>
  )
}
