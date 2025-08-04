'use client'

import { 
  DocumentTextIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

interface MarkerStatsProps {
  data?: {
    total: number
    active: number
    by_type: Record<string, number>
    recently_updated: number
  }
}

const COLORS: Record<string, string> = {
  'A': '#3B82F6',
  'S': '#10B981',
  'C': '#8B5CF6',
  'MM': '#EF4444',
  'Other': '#6B7280'
}

export function MarkerStats({ data }: MarkerStatsProps) {
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

  const chartData = Object.entries(data.by_type).map(([type, count]) => ({
    name: type,
    value: count,
  }))

  const activePercentage = data.total > 0 
    ? Math.round((data.active / data.total) * 100) 
    : 0

  return (
    <div className="dashboard-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Marker Statistics</h3>
        <DocumentTextIcon className="h-5 w-5 text-gray-400" />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-500">Total Markers</p>
          <p className="text-2xl font-semibold text-gray-900">{data.total}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Active</p>
          <p className="text-2xl font-semibold text-green-600">
            {data.active} ({activePercentage}%)
          </p>
        </div>
      </div>

      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={25}
              outerRadius={50}
              paddingAngle={5}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[entry.name] || COLORS.Other} 
                />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-500">Recently Updated</span>
          </div>
          <span className="text-sm font-medium text-gray-900">
            {data.recently_updated}
          </span>
        </div>
      </div>
    </div>
  )
}