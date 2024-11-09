import '@/styles/globals.css'
import { Libre_Franklin } from 'next/font/google'
import { Toaster } from "@/components/ui/toaster"

const libreFranklin = Libre_Franklin({ 
  weight: ['300', '400', '500', '600', '700'],
  subsets: ['latin'] 
})

export const metadata = {
  title: 'NBA Connections Game',
  description: 'A daily NBA-themed connections puzzle game',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={libreFranklin.className}>
        {children}
        <Toaster />
      </body>
    </html>
  )
}