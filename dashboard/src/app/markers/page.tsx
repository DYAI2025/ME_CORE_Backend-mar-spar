'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MarkerList } from '@/components/markers/MarkerList'
import { DetectRegistryEditor } from '@/components/markers/DetectRegistryEditor'
import { SchemaViewer } from '@/components/markers/SchemaViewer'
import { MarkerSearch } from '@/components/markers/MarkerSearch'
import { fetchMarkers, fetchDetectRegistry, fetchSchemas } from '@/lib/api'
import { Tab } from '@headlessui/react'
import clsx from 'clsx'

export default function MarkersPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const queryClient = useQueryClient()

  const { data: markers, isLoading: markersLoading } = useQuery({
    queryKey: ['markers'],
    queryFn: fetchMarkers,
  })

  const { data: registry, isLoading: registryLoading } = useQuery({
    queryKey: ['detect-registry'],
    queryFn: fetchDetectRegistry,
  })

  const { data: schemas, isLoading: schemasLoading } = useQuery({
    queryKey: ['schemas'],
    queryFn: fetchSchemas,
  })

  const filteredMarkers = markers?.filter(marker => 
    marker.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    marker.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Marker Management</h1>
        <MarkerSearch value={searchTerm} onChange={setSearchTerm} />
      </div>

      <Tab.Group>
        <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1">
          <Tab
            className={({ selected }) =>
              clsx(
                'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                selected
                  ? 'bg-white text-blue-700 shadow'
                  : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
              )
            }
          >
            Active Markers ({markers?.length || 0})
          </Tab>
          <Tab
            className={({ selected }) =>
              clsx(
                'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                selected
                  ? 'bg-white text-blue-700 shadow'
                  : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
              )
            }
          >
            DETECT Registry
          </Tab>
          <Tab
            className={({ selected }) =>
              clsx(
                'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                selected
                  ? 'bg-white text-blue-700 shadow'
                  : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
              )
            }
          >
            Schemas
          </Tab>
        </Tab.List>
        <Tab.Panels className="mt-6">
          <Tab.Panel>
            {markersLoading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <MarkerList markers={filteredMarkers || []} />
            )}
          </Tab.Panel>
          <Tab.Panel>
            {registryLoading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <DetectRegistryEditor registry={registry} />
            )}
          </Tab.Panel>
          <Tab.Panel>
            {schemasLoading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <SchemaViewer schemas={schemas || []} />
            )}
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  )
}