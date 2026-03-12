import { useEffect, useRef } from 'react'
import { usePipeline } from '../../hooks/usePipeline'
import { PipelineProgress } from './PipelineProgress'

interface PipelineRunnerProps {
  jdId: string
  onComplete?: () => void
}

export const PipelineRunner = ({ jdId, onComplete }: PipelineRunnerProps) => {
  const pipeline = usePipeline()
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true

    pipeline.run(jdId).then(() => onComplete?.())
  }, [jdId, onComplete, pipeline])

  return <PipelineProgress steps={pipeline.steps} />
}
