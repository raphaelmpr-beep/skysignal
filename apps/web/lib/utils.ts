import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow, parseISO } from 'date-fns'
import type { Severity, ConfidenceTier, ReviewStatus, ThreatTier, EvidenceRole } from './types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string, fmt = 'MMM d, yyyy') {
  try {
    return format(parseISO(dateStr), fmt)
  } catch {
    return dateStr
  }
}

export function formatDateTime(dateStr: string) {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy HH:mm')
  } catch {
    return dateStr
  }
}

export function formatRelativeTime(dateStr: string) {
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true })
  } catch {
    return dateStr
  }
}

export function formatConfidence(score: number) {
  return `${Math.round(score * 100)}%`
}

export function formatScore(score: number) {
  return score.toFixed(1)
}

// Severity colors
export function getSeverityColor(severity: Severity): string {
  switch (severity) {
    case 'CRITICAL': return '#EF4444' // red
    case 'HIGH': return '#E05C1A'     // orange-alert
    case 'MEDIUM': return '#F0A500'   // amber-pending
    case 'LOW': return '#00B4C8'      // teal
    case 'UNKNOWN': return '#8A9BB5'  // muted
    default: return '#8A9BB5'
  }
}

export function getSeverityBg(severity: Severity): string {
  switch (severity) {
    case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/30'
    case 'HIGH': return 'bg-orange-alert/20 text-orange-400 border-orange-alert/30'
    case 'MEDIUM': return 'bg-amber-pending/20 text-amber-400 border-amber-pending/30'
    case 'LOW': return 'bg-teal/20 text-teal border-teal/30'
    case 'UNKNOWN': return 'bg-white/10 text-muted-foreground border-white/10'
    default: return 'bg-white/10 text-muted-foreground border-white/10'
  }
}

// Confidence tier colors
export function getConfidenceColor(tier: ConfidenceTier): string {
  switch (tier) {
    case 'VERY_HIGH': return '#2E9E5B'
    case 'HIGH': return '#00B4C8'
    case 'MEDIUM': return '#F0A500'
    case 'LOW': return '#E05C1A'
    case 'VERY_LOW': return '#EF4444'
    default: return '#8A9BB5'
  }
}

export function getConfidenceBg(tier: ConfidenceTier): string {
  switch (tier) {
    case 'VERY_HIGH': return 'bg-green-confirmed/20 text-green-400 border-green-confirmed/30'
    case 'HIGH': return 'bg-teal/20 text-teal border-teal/30'
    case 'MEDIUM': return 'bg-amber-pending/20 text-amber-400 border-amber-pending/30'
    case 'LOW': return 'bg-orange-alert/20 text-orange-400 border-orange-alert/30'
    case 'VERY_LOW': return 'bg-red-500/20 text-red-400 border-red-500/30'
    default: return 'bg-white/10 text-muted-foreground border-white/10'
  }
}

// Review status colors
export function getStatusBg(status: ReviewStatus): string {
  switch (status) {
    case 'APPROVED': return 'bg-green-confirmed/20 text-green-400 border-green-confirmed/30'
    case 'PENDING': return 'bg-amber-pending/20 text-amber-400 border-amber-pending/30'
    case 'REJECTED': return 'bg-red-500/20 text-red-400 border-red-500/30'
    case 'UNDER_REVIEW': return 'bg-teal/20 text-teal border-teal/30'
    default: return 'bg-white/10 text-muted-foreground border-white/10'
  }
}

// Threat tier colors
export function getTierColor(tier: ThreatTier): string {
  switch (tier) {
    case 'MINIMAL': return '#8A9BB5'
    case 'LOW': return '#00B4C8'
    case 'MODERATE': return '#F0A500'
    case 'ELEVATED': return '#E05C1A'
    case 'HIGH': return '#EF4444'
    default: return '#8A9BB5'
  }
}

export function getTierBg(tier: ThreatTier): string {
  switch (tier) {
    case 'MINIMAL': return 'bg-white/10 text-slate-400 border-white/10'
    case 'LOW': return 'bg-teal/20 text-teal border-teal/30'
    case 'MODERATE': return 'bg-amber-pending/20 text-amber-400 border-amber-pending/30'
    case 'ELEVATED': return 'bg-orange-alert/20 text-orange-400 border-orange-alert/30'
    case 'HIGH': return 'bg-red-500/20 text-red-400 border-red-500/30'
    default: return 'bg-white/10 text-muted-foreground border-white/10'
  }
}

export function getThreatTierFromScore(score: number): ThreatTier {
  if (score <= 20) return 'MINIMAL'
  if (score <= 40) return 'LOW'
  if (score <= 60) return 'MODERATE'
  if (score <= 80) return 'ELEVATED'
  return 'HIGH'
}

// Evidence role colors
export function getEvidenceRoleBg(role: EvidenceRole): string {
  switch (role) {
    case 'OFFICIAL_CONFIRMATION': return 'bg-green-confirmed/20 text-green-400 border-green-confirmed/30'
    case 'CORROBORATION': return 'bg-teal/20 text-teal border-teal/30'
    case 'DISCOVERY': return 'bg-white/10 text-slate-400 border-white/10'
    case 'CONTRADICTION': return 'bg-red-500/20 text-red-400 border-red-500/30'
    default: return 'bg-white/10 text-muted-foreground border-white/10'
  }
}

// Leaflet marker colors
export function getSeverityMarkerColor(severity: Severity): string {
  switch (severity) {
    case 'CRITICAL': return '#EF4444'
    case 'HIGH': return '#E05C1A'
    case 'MEDIUM': return '#F0A500'
    case 'LOW': return '#3B82F6'
    case 'UNKNOWN': return '#6B7280'
    default: return '#6B7280'
  }
}

export function truncate(str: string, length = 80): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function formatMiles(miles: number): string {
  return miles === 1 ? '1 mile' : `${miles} miles`
}

export function formatDays(days: number): string {
  if (days < 30) return `${days} days`
  if (days < 365) return `${Math.round(days / 30)} months`
  const years = Math.round(days / 365)
  return years === 1 ? '1 year' : `${years} years`
}
