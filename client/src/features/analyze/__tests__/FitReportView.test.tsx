import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { FitReport, JobDescription, ResumeVariant } from '../../../types'
import { FitReportView } from '../FitReportView'

const base: FitReport = {
  id: 'fr-1',
  userId: 'u',
  jobDescriptionId: 'jd-1',
  fitLevel: 'strong',
  matches: [],
  gaps: [],
  terminology: [],
  reasoning: 'Solid alignment.',
  overallScore: 0.84,
  semanticScore: 0.81,
  culturalSignals: [{ quality: 'ownership', jdSignal: 'you drive it', evidenceHint: 'look for X' }],
  productConnection: null,
  createdAt: '2026-07-03',
}

describe('FitReportView gate (#31)', () => {
  it('offers primary generation when fit is clean', () => {
    render(<FitReportView jdId="jd-1" fitReport={base} resume={null} onGenerate={vi.fn()} />)
    expect(screen.getByRole('button', { name: /generate resume/i })).toBeInTheDocument()
    expect(screen.queryByText(/hard gap/i)).not.toBeInTheDocument()
  })

  it('blocks with override when hard gaps exist', () => {
    const gated: FitReport = {
      ...base,
      fitLevel: 'poor',
      gaps: [{ requirement: 'iOS', type: 'hard', notes: 'none' }],
    }
    render(<FitReportView jdId="jd-1" fitReport={gated} resume={null} onGenerate={vi.fn()} />)
    expect(screen.getByText(/1 hard gap/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /generate anyway/i })).toBeInTheDocument()
  })

  it('renders cultural signals (#32)', () => {
    render(<FitReportView jdId="jd-1" fitReport={base} resume={null} onGenerate={vi.fn()} />)
    expect(screen.getByText('ownership')).toBeInTheDocument()
  })

  it('renders the annotated JD when jobDescription is provided', () => {
    const jd: JobDescription = {
      id: 'jd-1',
      userId: 'u',
      title: 'Senior Frontend Engineer',
      company: 'Acme',
      content: 'We need a frontend engineer who ships React features weekly.',
      createdAt: '2026-07-03',
    }
    render(
      <FitReportView
        jdId="jd-1"
        fitReport={base}
        resume={null}
        onGenerate={vi.fn()}
        jobDescription={jd}
      />,
    )
    expect(screen.getByText(/ships React features weekly/i)).toBeInTheDocument()
  })

  it('never renders a generation CTA when a resume exists', () => {
    const resume: ResumeVariant = {
      id: 'rv-1',
      userId: 'u',
      jobDescriptionId: 'jd-1',
      content: '## Summary',
      version: 1,
      parentVariantId: null,
      screenerReport: {
        screenerAnalysis: {
          keywordCoverage: {},
          semanticScore: 0.8,
          coverageGaps: [],
          terminologyMismatches: [],
          overallScore: 0.8,
        },
        refinementChanges: {
          sectionsModified: [],
          changes: [],
          remainingGaps: [],
          coverageImprovement: 0,
        },
      },
      createdAt: '2026-07-03',
    }
    const gated: FitReport = {
      ...base,
      fitLevel: 'poor',
      gaps: [{ requirement: 'iOS', type: 'hard', notes: 'none' }],
    }
    // Clean fit: primary CTA must not appear once a resume exists.
    const { unmount } = render(
      <FitReportView jdId="jd-1" fitReport={base} resume={resume} onGenerate={vi.fn()} />,
    )
    expect(screen.queryByRole('button', { name: /generate resume/i })).not.toBeInTheDocument()
    unmount()
    // Blocked fit: the gate override must not appear either.
    render(<FitReportView jdId="jd-1" fitReport={gated} resume={resume} onGenerate={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /generate anyway/i })).not.toBeInTheDocument()
  })
})
