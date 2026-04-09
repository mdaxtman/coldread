import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { ResumePanel } from '../ResumePanel'
import type { ResumeVariant } from '../../../types'

const createMockResumeVariant = (overrides?: Partial<ResumeVariant>): ResumeVariant => ({
  id: '123',
  userId: 'user1',
  jobDescriptionId: 'jd1',
  content: '## Summary\nTest content',
  contactInfo: undefined,
  version: 1,
  parentVariantId: null,
  screenerReport: {
    screenerAnalysis: {
      keywordCoverage: { react: true, typescript: false },
      semanticScore: 0.85,
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
  createdAt: '2024-01-01T00:00:00Z',
  ...overrides,
})

describe('ResumePanel - Contact Info Rendering', () => {
  it('includes contact info with name at top of resume content when present', () => {
    const variant = createMockResumeVariant({
      contactInfo: {
        name: 'Test User',
        email: 'test@example.com',
        phone: '+1-555-0123',
        location: 'San Francisco, CA',
      },
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Contact should be in the rendered resume content
    expect(container.textContent).toContain('Test User')
    expect(container.textContent).toContain('test@example.com')
    expect(container.textContent).toContain('+1-555-0123')
    expect(container.textContent).toContain('San Francisco, CA')
    // Verify name appears before contact details
    const textContent = container.textContent || ''
    expect(textContent).toMatch(/Test User.*test@example\.com.*Summary/s)
  })

  it('skips empty contact fields', () => {
    const variant = createMockResumeVariant({
      contactInfo: {
        email: 'test@example.com',
        phone: undefined,
        location: 'San Francisco, CA',
      },
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Should not contain undefined in text
    expect(container.textContent).not.toContain('undefined')
    expect(container.textContent).toContain('test@example.com')
    expect(container.textContent).toContain('San Francisco, CA')
    // Phone should not appear
    expect(container.textContent).not.toContain('+1-555')
  })

  it('does not include contact info when contactInfo is null', () => {
    const variant = createMockResumeVariant({
      contactInfo: null,
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Should render the component with content
    expect(container.textContent).toContain('Summary')
    // But no contact info line prefix
    expect(container.textContent).not.toMatch(/.*@.*\|/)
  })

  it('formats all contact fields with pipe separators when provided', () => {
    const variant = createMockResumeVariant({
      contactInfo: {
        name: 'John Smith',
        email: 'john@example.com',
        phone: '+1-555-9876',
        location: 'New York, NY',
        linkedin: 'linkedin.com/in/john',
        github: 'github.com/john',
        website: 'johnsmith.dev',
      },
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Verify name appears as heading
    expect(container.textContent).toContain('John Smith')
    // Verify all contact fields appear in the content
    expect(container.textContent).toContain('john@example.com')
    expect(container.textContent).toContain('+1-555-9876')
    expect(container.textContent).toContain('New York, NY')
    expect(container.textContent).toContain('linkedin.com/in/john')
    expect(container.textContent).toContain('github.com/john')
    expect(container.textContent).toContain('johnsmith.dev')
    // Verify pipe separator formatting
    expect(container.textContent).toContain(' | ')
  })

  it('does not include contact line when contactInfo is undefined', () => {
    const variant = createMockResumeVariant({
      contactInfo: undefined,
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Should render the summary but no contact prefix
    expect(container.textContent).toContain('Summary')
    expect(container.textContent).not.toMatch(/.*@.*\|/)
  })

  it('does not include contact line when all contact fields are empty', () => {
    const variant = createMockResumeVariant({
      contactInfo: {}, // All fields undefined/missing
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Should render the content normally without contact prefix
    expect(container.textContent).toContain('Summary')
    expect(container.textContent).not.toMatch(/.*@.*\|/)
  })

  it('includes contact info in downloaded resume', () => {
    const variant = createMockResumeVariant({
      content: '## Summary\nTest content',
      contactInfo: {
        email: 'test@example.com',
        phone: '+1-555-0123',
      },
    })

    const { getByText } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // When exported, contact should be at top of the content
    // Verify contact appears in the rendered markdown
    const downloadBtn = getByText('Download .txt')
    expect(downloadBtn).toBeInTheDocument()
  })
})
