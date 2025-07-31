'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface Marker {
  id: string
  type: string
  description?: string
  keywords?: string[]
  pattern?: string
  confidence: number
  category?: string
  active: boolean
}

interface MarkerListProps {
  markers: Marker[]
}

export function MarkerList({ markers }: MarkerListProps) {
  const [expandedMarkers, setExpandedMarkers] = useState<Set<string>>(new Set())
  const [selectedType, setSelectedType] = useState<string>('all')

  const markerTypes = ['all', ...new Set(markers.map(m => m.type))]
  const filteredMarkers = selectedType === 'all' 
    ? markers 
    : markers.filter(m => m.type === selectedType)

  const toggleExpanded = (markerId: string) => {
    const newExpanded = new Set(expandedMarkers)
    if (newExpanded.has(markerId)) {
      newExpanded.delete(markerId)
    } else {
      newExpanded.add(markerId)
    }
    setExpandedMarkers(newExpanded)
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'A': 'bg-blue-100 text-blue-800',
      'S': 'bg-green-100 text-green-800',
      'C': 'bg-purple-100 text-purple-800',
      'MM': 'bg-red-100 text-red-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <label className="text-sm font-medium text-gray-700">Filter by type:</label>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
        >
          {markerTypes.map(type => (
            <option key={type} value={type}>
              {type === 'all' ? 'All Types' : type}
            </option>
          ))}
        </select>
        <div className="text-sm text-gray-500">
          Showing {filteredMarkers.length} of {markers.length} markers
        </div>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredMarkers.map((marker) => (
            <li key={marker.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <button
                      onClick={() => toggleExpanded(marker.id)}
                      className="mr-3 text-gray-400 hover:text-gray-600"
                    >
                      {expandedMarkers.has(marker.id) ? (
                        <ChevronDownIcon className="h-5 w-5" />
                      ) : (
                        <ChevronRightIcon className="h-5 w-5" />
                      )}
                    </button>
                    <div>
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">
                          {marker.id}
                        </p>
                        <span className={clsx(
                          'ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          getTypeColor(marker.type)
                        )}>
                          {marker.type}
                        </span>
                        <span className={clsx(
                          'ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          marker.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        )}>
                          {marker.active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      {marker.description && (
                        <p className="mt-1 text-sm text-gray-500">
                          {marker.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    Confidence: {(marker.confidence * 100).toFixed(0)}%
                  </div>
                </div>

                {expandedMarkers.has(marker.id) && (
                  <div className="mt-4 ml-8 space-y-2">
                    {marker.keywords && marker.keywords.length > 0 && (
                      <div>
                        <span className="text-sm font-medium text-gray-700">Keywords:</span>
                        <div className="mt-1 flex flex-wrap gap-2">
                          {marker.keywords.map((keyword, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {marker.pattern && (
                      <div>
                        <span className="text-sm font-medium text-gray-700">Pattern:</span>
                        <code className="mt-1 block text-xs bg-gray-100 p-2 rounded">
                          {marker.pattern}
                        </code>
                      </div>
                    )}
                    {marker.category && (
                      <div>
                        <span className="text-sm font-medium text-gray-700">Category:</span>
                        <span className="ml-2 text-sm text-gray-500">{marker.category}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}