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
  // Core UI
  export const Shield: LucideIcon
  export const ShieldAlert: LucideIcon
  export const ShieldCheck: LucideIcon
  export const Map: LucideIcon
  export const Activity: LucideIcon
  export const AlertTriangle: LucideIcon
  export const AlertOctagon: LucideIcon
  export const AlertCircle: LucideIcon
  export const BarChart: LucideIcon
  export const BarChart2: LucideIcon
  export const BarChart3: LucideIcon
  export const BarChart4: LucideIcon
  export const BarChartHorizontal: LucideIcon
  export const BarChartBig: LucideIcon
  export const FileText: LucideIcon
  export const Settings: LucideIcon
  export const Users: LucideIcon
  export const Database: LucideIcon
  export const Search: LucideIcon
  export const Filter: LucideIcon
  export const Plus: LucideIcon
  export const Eye: LucideIcon
  export const EyeOff: LucideIcon
  export const Download: LucideIcon
  export const Upload: LucideIcon
  export const Check: LucideIcon
  export const CheckCircle: LucideIcon
  export const CheckCircle2: LucideIcon
  export const CheckSquare: LucideIcon
  export const X: LucideIcon
  export const XCircle: LucideIcon
  export const XSquare: LucideIcon
  export const ChevronDown: LucideIcon
  export const ChevronUp: LucideIcon
  export const ChevronLeft: LucideIcon
  export const ChevronRight: LucideIcon
  export const ArrowUp: LucideIcon
  export const ArrowDown: LucideIcon
  export const ArrowLeft: LucideIcon
  export const ArrowRight: LucideIcon
  export const ArrowLeftRight: LucideIcon
  export const Bell: LucideIcon
  export const LogOut: LucideIcon
  export const User: LucideIcon
  export const MapPin: LucideIcon
  export const Crosshair: LucideIcon
  export const CrosshairIcon: LucideIcon
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
  export const Trash2: LucideIcon
  export const Edit: LucideIcon
  export const Edit2: LucideIcon
  export const Edit3: LucideIcon
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
  // Navigation & layout
  export const LayoutDashboard: LucideIcon
  export const LayoutGrid: LucideIcon
  export const LayoutList: LucideIcon
  export const Layout: LucideIcon
  // Sources page
  export const Globe: LucideIcon
  export const Globe2: LucideIcon
  export const GlobeLock: LucideIcon
  export const ToggleLeft: LucideIcon
  export const ToggleRight: LucideIcon
  // Auth
  export const Key: LucideIcon
  export const KeyRound: LucideIcon
  export const Save: LucideIcon
  export const SaveAll: LucideIcon
  // Dates
  export const Calendar: LucideIcon
  export const CalendarDays: LucideIcon
  export const CalendarCheck: LucideIcon
  export const CalendarRange: LucideIcon
  // Misc
  export const Bookmark: LucideIcon
  export const BookmarkCheck: LucideIcon
  export const Minus: LucideIcon
  export const MinusCircle: LucideIcon
  export const GitMerge: LucideIcon
  export const GitBranch: LucideIcon
  export const Thermometer: LucideIcon
  export const ThermometerSun: LucideIcon
  export const ThermometerSnowflake: LucideIcon
  export const Crosshair: LucideIcon
  export const Cpu: LucideIcon
  export const Smartphone: LucideIcon
  export const Plane: LucideIcon
  export const PlaneTakeoff: LucideIcon
  export const PlaneLanding: LucideIcon
  export const Radio: LucideIcon
  export const Signal: LucideIcon
  export const Radar: LucideIcon
  export const Scan: LucideIcon
  export const ScanLine: LucideIcon
  export const Network: LucideIcon
  export const Share: LucideIcon
  export const Share2: LucideIcon
  export const Link: LucideIcon
  export const Link2: LucideIcon
  export const Unlink: LucideIcon
  export const Power: LucideIcon
  export const PowerOff: LucideIcon
  export const RotateCcw: LucideIcon
  export const RotateCw: LucideIcon
  export const Refresh: LucideIcon
}
