import type { Metadata } from 'next'
import { Providers } from '@/components/Providers'
import { Navigation } from '@/components/Navigation'
import { Toaster } from 'react-hot-toast'
import './globals.css'

export const metadata: Metadata = {
  title: 'MarkerEngine Core Dashboard',
  description: 'Monitoring and management dashboard for MarkerEngine Core',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          <div className="min-h-screen bg-gray-50">
            <Navigation />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {children}
            </main>
          </div>
          <Toaster position="top-right" />
        </Providers>
      </body>
    </html>
  )
}