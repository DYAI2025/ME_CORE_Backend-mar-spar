'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchJenkinsStatus } from '@/lib/api'
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface JenkinsStatusProps {
  data?: any
}

export function JenkinsStatus({ data: initialData }: JenkinsStatusProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['jenkins-status'],
    queryFn: fetchJenkinsStatus,
    initialData,
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  if (isLoading) {
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

  if (error || !data) {
    return (
      <div className="dashboard-card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Jenkins CI/CD</h3>
        <div className="text-red-600 text-sm">Failed to load Jenkins status</div>
      </div>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'FAILURE':
        return <XCircleIcon className="h-5 w-5 text-red-500" />
      case 'IN_PROGRESS':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'text-green-600'
      case 'FAILURE':
        return 'text-red-600'
      case 'IN_PROGRESS':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="dashboard-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Jenkins CI/CD</h3>
        <span className={clsx(
          'status-indicator',
          data.healthy ? 'success' : 'error'
        )}>
          {data.healthy ? 'Healthy' : 'Unhealthy'}
        </span>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Queue Size</span>
          <span className="text-sm font-medium">{data.queueSize || 0}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Executors</span>
          <span className="text-sm font-medium">
            {data.busyExecutors || 0} / {data.totalExecutors || 0}
          </span>
        </div>
      </div>

      {data.recentBuilds && data.recentBuilds.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Recent Builds</h4>
          <div className="space-y-2">
            {data.recentBuilds.slice(0, 3).map((build: any, index: number) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(build.result)}
                  <span className="text-sm text-gray-700 truncate max-w-[150px]">
                    {build.displayName}
                  </span>
                </div>
                <span className={clsx('text-xs', getStatusColor(build.result))}>
                  {build.result}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}