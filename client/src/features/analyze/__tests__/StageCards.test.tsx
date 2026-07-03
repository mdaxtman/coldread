import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StageCards } from '../StageCards'

describe('StageCards', () => {
  it('shows running and done states', () => {
    render(
      <StageCards
        stages={[
          {
            stage: 'fit',
            seq: 1,
            status: 'done',
            model: 'claude-sonnet-4-20250514',
            tokensOut: 1102,
            latencyMs: 2140,
          },
          { stage: 'generate', seq: 2, status: 'running' },
        ]}
      />,
    )
    expect(screen.getByText('fit')).toBeInTheDocument()
    expect(screen.getByText(/2140/)).toBeInTheDocument()
    expect(screen.getByText('generate')).toBeInTheDocument()
  })
})
