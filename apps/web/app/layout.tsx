import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SkySignal — Drone Threat Intelligence',
  description: 'Advanced drone threat intelligence and facility risk assessment platform',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-navy text-foreground antialiased">
        {children}
      </body>
    </html>
  )
}
