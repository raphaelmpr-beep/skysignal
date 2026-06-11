declare module 'lucide-react' {
  import * as React from 'react'
  export type LucideIcon = React.ForwardRefExoticComponent<
    React.PropsWithoutRef<React.SVGProps<SVGSVGElement>> & {
      size?: number | string
      absoluteStrokeWidth?: boolean
    } & React.RefAttributes<SVGSVGElement>
  >
  // Named exports for every icon — catch-all
  const _default: { [key: string]: LucideIcon }
  export default _default
  export const Shield: LucideIcon
  export const Map: LucideIcon
  export const Activity: LucideIcon
  export const AlertTriangle: LucideIcon
  export const BarChart2: LucideIcon
  export const FileText: LucideIcon
  export const Settings: LucideIcon
  export const Users: LucideIcon
  export const Database: LucideIcon
  export const Search: LucideIcon
  export const Filter: LucideIcon
  export const Plus: LucideIcon
  export const Eye: LucideIcon
  export const Download: LucideIcon
  export const Upload: LucideIcon
  export const Check: LucideIcon
  export const X: LucideIcon
  export const ChevronDown: LucideIcon
  export const ChevronUp: LucideIcon
  export const ChevronLeft: LucideIcon
  export const ChevronRight: LucideIcon
  export const ArrowUp: LucideIcon
  export const ArrowDown: LucideIcon
  export const Bell: LucideIcon
  export const LogOut: LucideIcon
  export const User: LucideIcon
  export const MapPin: LucideIcon
  export const Crosshair: LucideIcon
  export const Loader2: LucideIcon
  export const RefreshCw: LucideIcon
  export const Info: LucideIcon
  export const ExternalLink: LucideIcon
  export const Layers: LucideIcon
  export const Target: LucideIcon
  export const Zap: LucideIcon
  export const Clock: LucideIcon
  export const TrendingUp: LucideIcon
  export const TrendingDown: LucideIcon
  export const Circle: LucideIcon
  export const Radio: LucideIcon
  export const Clipboard: LucideIcon
  export const List: LucideIcon
  export const Home: LucideIcon
  export const Lock: LucideIcon
  export const Mail: LucideIcon
  export const Send: LucideIcon
  export const Star: LucideIcon
  export const Trash: LucideIcon
  export const Edit: LucideIcon
  export const Copy: LucideIcon
  export const Menu: LucideIcon
  export const MoreVertical: LucideIcon
  export const MoreHorizontal: LucideIcon
  export const Navigation: LucideIcon
  export const Maximize: LucideIcon
  export const Minimize: LucideIcon
  export const Flag: LucideIcon
  export const Tag: LucideIcon
  export const Building: LucideIcon
  export const Building2: LucideIcon
  export const Satellite: LucideIcon
  export const Wifi: LucideIcon
  export const WifiOff: LucideIcon
}
