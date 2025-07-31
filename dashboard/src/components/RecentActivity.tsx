'use client'

import { formatDistanceToNow } from 'date-fns'
import { 
  CheckCircleIcon,
  PencilSquareIcon,
  TrashIcon,
  ArrowUpTrayIcon,
  CogIcon
} from '@heroicons/react/24/outline'

interface Activity {
  id: string
  timestamp: string
  type: string
  message: string
  metadata?: any
}

interface RecentActivityProps {
  activities: Activity[]
}

export function RecentActivity({ activities }: RecentActivityProps) {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'marker_created':
      case 'marker_updated':
        return <PencilSquareIcon className="h-5 w-5 text-blue-500" />
      case 'marker_deleted':
        return <TrashIcon className="h-5 w-5 text-red-500" />
      case 'registry_update':
        return <ArrowUpTrayIcon className="h-5 w-5 text-green-500" />
      case 'deployment_triggered':
        return <CogIcon className="h-5 w-5 text-purple-500" />
      default:
        return <CheckCircleIcon className="h-5 w-5 text-gray-500" />
    }
  }

  if (activities.length === 0) {
    return (
      <div className="dashboard-card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
        <p className="text-sm text-gray-500 text-center py-8">
          No recent activity to display
        </p>
      </div>
    )
  }

  return (
    <div className="dashboard-card">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
      <div className="flow-root">
        <ul className="-mb-8">
          {activities.map((activity, activityIdx) => (
            <li key={activity.id}>
              <div className="relative pb-8">
                {activityIdx !== activities.length - 1 ? (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                ) : null}
                <div className="relative flex space-x-3">
                  <div>
                    <span className="h-8 w-8 rounded-full flex items-center justify-center bg-gray-100">
                      {getActivityIcon(activity.type)}
                    </span>
                  </div>
                  <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                    <div>
                      <p className="text-sm text-gray-900">{activity.message}</p>
                    </div>
                    <div className="whitespace-nowrap text-right text-xs text-gray-500">
                      {formatDistanceToNow(new Date(activity.timestamp), { 
                        addSuffix: true 
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}