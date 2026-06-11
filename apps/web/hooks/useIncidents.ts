'use client'

import { useState, useEffect, useCallback } from 'react'
import { fetchIncidents } from '@/lib/api'
import type { Incident, IncidentFilters, PaginatedResponse } from '@/lib/types'

interface UseIncidentsResult {
  incidents: Incident[]
  total: number
  page: number
  pages: number
  isLoading: boolean
  error: string | null
  setFilters: (filters: IncidentFilters) => void
  setPage: (page: number) => void
  refresh: () => void
}

export function useIncidents(initialFilters: IncidentFilters = {}): UseIncidentsResult {
  const [filters, setFiltersState] = useState<IncidentFilters>({
    per_page: 50,
    page: 1,
    ...initialFilters,
  })
  const [data, setData] = useState<PaginatedResponse<Incident> | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await fetchIncidents(filters)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load incidents')
    } finally {
      setIsLoading(false)
    }
  }, [filters])

  useEffect(() => {
    load()
  }, [load])

  const setFilters = (newFilters: IncidentFilters) => {
    setFiltersState((prev) => ({ ...prev, ...newFilters, page: 1 }))
  }

  const setPage = (page: number) => {
    setFiltersState((prev) => ({ ...prev, page }))
  }

  return {
    incidents: data?.items || [],
    total: data?.total || 0,
    page: data?.page || 1,
    pages: data?.pages || 1,
    isLoading,
    error,
    setFilters,
    setPage,
    refresh: load,
  }
}
