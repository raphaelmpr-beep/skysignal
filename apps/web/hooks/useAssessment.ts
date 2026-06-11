'use client'

import { useState, useEffect } from 'react'
import { fetchAssessment } from '@/lib/api'
import type { Assessment } from '@/lib/types'

interface UseAssessmentResult {
  assessment: Assessment | null
  isLoading: boolean
  error: string | null
  refresh: () => void
}

export function useAssessment(id: string): UseAssessmentResult {
  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    if (!id) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchAssessment(id)
      setAssessment(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assessment')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  return { assessment, isLoading, error, refresh: load }
}
