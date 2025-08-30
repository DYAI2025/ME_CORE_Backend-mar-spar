import type { Metadata } from 'next'
import Script from 'next/script'
import { Providers } from '@/components/Providers'
import { Navigation } from '@/components/Navigation'
import { Toaster } from 'react-hot-toast'
import './globals.css'

const inter = { className: "" };

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
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-gray-50">
            <Navigation />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {children}
            </main>
          </div>
          <Toaster position="top-right" />
        </Providers>
        <div id="dock"></div>
        <Script 
          src="https://b0bfe21bd-8080.preview.abacusai.app/sdk/inputdock.js" 
          strategy="afterInteractive"
        />
        <Script 
          src="/inputdock-init.js" 
          strategy="afterInteractive" 
        />
      </body>
    </html>
  )
}