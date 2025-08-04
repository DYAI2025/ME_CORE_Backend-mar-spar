'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  HomeIcon, 
  DocumentTextIcon, 
  CogIcon,
  ChartBarIcon,
  ServerIcon
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Markers', href: '/markers', icon: DocumentTextIcon },
  { name: 'CI/CD', href: '/ci', icon: ServerIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-primary-600">ME Core</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={clsx(
                      'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium',
                      isActive
                        ? 'border-primary-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                  >
                    <item.icon className="mr-2 h-5 w-5" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>
          <div className="flex items-center">
            <div className="flex items-center space-x-2">
              <div className="relative">
                <div className="absolute inset-0 bg-green-400 rounded-full animate-ping opacity-75"></div>
                <div className="relative bg-green-400 rounded-full h-3 w-3"></div>
              </div>
              <span className="text-sm text-gray-600">Connected</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}