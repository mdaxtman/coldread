import { Card } from '../../components/ui/Card'
import { FitSummary } from './FitSummary'
import { AnnotatedJd } from './AnnotatedJd'
import { GapsList } from './GapsList'
import { TerminologyTable } from './TerminologyTable'
import type { FitReport, JobDescription } from '../../types'
import styles from './SupportingPanel.module.css'

interface SupportingPanelProps {
  fitReport: FitReport
  jobDescription: JobDescription
  keywordCoverage: Record<string, boolean>
}

export function SupportingPanel({ fitReport, jobDescription, keywordCoverage }: SupportingPanelProps) {
  return (
    <div className={styles.panel}>
      <FitSummary report={fitReport} />

      <Card>
        <h3 className={styles.sectionHeading}>Job Description</h3>
        <AnnotatedJd content={jobDescription.content} keywordCoverage={keywordCoverage} />
      </Card>

      <GapsList gaps={fitReport.gaps} />

      <TerminologyTable terminology={fitReport.terminology} />
    </div>
  )
}
