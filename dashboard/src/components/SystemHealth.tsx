'use client'

import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  ClockIcon 
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface HealthData {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  components: {
    name: string
    status: 'healthy' | 'degraded' | 'unhealthy'
    latency?: number
    message?: string
  }[]
}

interface SystemHealthProps {
  data?: HealthData
}

export function SystemHealth({ data }: SystemHealthProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'degraded':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
      case 'unhealthy':
        return <XCircleIcon className="h-5 w-5 text-red-500" />
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800'
      case 'unhealthy':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (!data) {
    return (
      <div className="dashboard-card">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">System Health</h3>
        <span className={clsx(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
          getStatusColor(data.status)
        )}>
          {data.status.charAt(0).toUpperCase() + data.status.slice(1)}
        </span>
      </div>

      <div className="space-y-3">
        {data.components.map((component) => (
          <div key={component.name} className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {getStatusIcon(component.status)}
              <span className="text-sm text-gray-700">{component.name}</span>
            </div>
            <div className="flex items-center space-x-2">
              {component.latency && (
                <span className="text-xs text-gray-500">
                  {component.latency}ms
                </span>
              )}
              <span className={clsx(
                'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                getStatusColor(component.status)
              )}>
                {component.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Last checked: {new Date(data.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}