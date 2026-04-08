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
  it('renders contact info when present', () => {
    const variant = createMockResumeVariant({
      contactInfo: {
        email: 'test@example.com',
        phone: '+1-555-0123',
        location: 'San Francisco, CA',
      },
    })

    const { getByText } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    expect(getByText(/test@example\.com/)).toBeInTheDocument()
    expect(getByText(/\+1-555-0123/)).toBeInTheDocument()
    expect(getByText(/San Francisco, CA/)).toBeInTheDocument()
  })

  it('skips empty contact fields', () => {
    const variant = createMockResumeVariant({
      contactInfo: {
        email: 'test@example.com',
        phone: undefined,
        location: 'San Francisco, CA',
      },
    })

    const { container, getByText } = render(
      <ResumePanel resumeVariant={variant} fitLevel="strong" />,
    )

    // Should not contain undefined in text
    expect(container.textContent).not.toContain('undefined')
    expect(getByText(/test@example\.com/)).toBeInTheDocument()
    expect(getByText(/San Francisco, CA/)).toBeInTheDocument()
  })

  it('renders without contact section when contactInfo is null', () => {
    const variant = createMockResumeVariant({
      contactInfo: null,
    })

    const { container, getByText } = render(
      <ResumePanel resumeVariant={variant} fitLevel="strong" />,
    )

    // Should render the component
    expect(getByText(/Summary/)).toBeInTheDocument()

    // Contact region should not exist
    const contactRegion = container.querySelector('[aria-label="Contact information"]')
    expect(contactRegion).not.toBeInTheDocument()
  })

  it('handles all contact fields when provided', () => {
    const variant = createMockResumeVariant({
      contactInfo: {
        email: 'john@example.com',
        phone: '+1-555-9876',
        location: 'New York, NY',
        linkedin: 'linkedin.com/in/john',
        github: 'github.com/john',
        website: 'johnsmith.dev',
      },
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Verify contact region exists
    const contactRegion = container.querySelector('[aria-label="Contact information"]')
    expect(contactRegion).toBeInTheDocument()

    // Verify all fields are in the contact region
    expect(contactRegion?.textContent).toContain('john@example.com')
    expect(contactRegion?.textContent).toContain('+1-555-9876')
    expect(contactRegion?.textContent).toContain('New York, NY')
    expect(contactRegion?.textContent).toContain('linkedin.com/in/john')
    expect(contactRegion?.textContent).toContain('github.com/john')
    expect(contactRegion?.textContent).toContain('johnsmith.dev')
  })

  it('renders contact region with proper accessibility label', () => {
    const variant = createMockResumeVariant({
      contactInfo: {
        email: 'test@example.com',
      },
    })

    const { getByRole } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    const contactRegion = getByRole('region', { name: /Contact information/i })
    expect(contactRegion).toBeInTheDocument()
  })

  it('does not render contact region when contactInfo is undefined', () => {
    const variant = createMockResumeVariant({
      contactInfo: undefined,
    })

    const { queryByRole } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    const contactRegion = queryByRole('region', { name: /Contact information/i })
    expect(contactRegion).not.toBeInTheDocument()
  })

  it('handles empty contact object', () => {
    const variant = createMockResumeVariant({
      contactInfo: {}, // All fields undefined/missing
    })

    const { container } = render(<ResumePanel resumeVariant={variant} fitLevel="strong" />)

    // Contact region should not render if all fields are empty
    const contactRegion = container.querySelector('[aria-label="Contact information"]')
    expect(contactRegion).not.toBeInTheDocument()
  })
})
