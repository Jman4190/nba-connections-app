import { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3001'

export const metadata: Metadata = {
  metadataBase: new URL(baseUrl),
  title: 'NBA Connections',
  description: 'Group NBA players that share a common thread.',
  openGraph: {
    title: 'NBA Connections',
    description: 'Group NBA players that share a common thread.',
    url: baseUrl,
    siteName: 'NBA Connections',
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    title: 'NBA Connections',
    description: 'Group NBA players that share a common thread.',
    card: 'summary_large_image',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="NBA Connections" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  )
}