'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Menu } from '@headlessui/react'
import { 
  ChevronDownIcon,
  PlayIcon,
  ArrowUpTrayIcon,
  BeakerIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { triggerDeployment, triggerE2ETests } from '@/lib/api'

export function QuickActions() {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<{
    type: string
    environment?: string
  } | null>(null)

  const deployMutation = useMutation({
    mutationFn: (environment: string) => triggerDeployment(environment as 'staging' | 'production'),
    onSuccess: (data) => {
      toast.success(`Deployment to ${pendingAction?.environment} initiated`)
      setIsConfirmOpen(false)
      setPendingAction(null)
    },
    onError: (error: any) => {
      toast.error(error.message || 'Deployment failed')
    },
  })

  const testMutation = useMutation({
    mutationFn: triggerE2ETests,
    onSuccess: (data) => {
      toast.success('E2E tests triggered')
      setIsConfirmOpen(false)
      setPendingAction(null)
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to trigger tests')
    },
  })

  const handleAction = (type: string, environment?: string) => {
    setPendingAction({ type, environment })
    setIsConfirmOpen(true)
  }

  const confirmAction = () => {
    if (!pendingAction) return

    switch (pendingAction.type) {
      case 'deploy':
        if (pendingAction.environment) {
          deployMutation.mutate(pendingAction.environment)
        }
        break
      case 'test':
        testMutation.mutate()
        break
    }
  }

  return (
    <>
      <Menu as="div" className="relative inline-block text-left">
        <div>
          <Menu.Button className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
            Quick Actions
            <ChevronDownIcon className="ml-2 -mr-1 h-5 w-5" aria-hidden="true" />
          </Menu.Button>
        </div>

        <Menu.Items className="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={() => handleAction('deploy', 'staging')}
                  className={`${
                    active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                  } group flex w-full items-center px-4 py-2 text-sm`}
                >
                  <ArrowUpTrayIcon className="mr-3 h-5 w-5 text-gray-400" />
                  Deploy to Staging
                </button>
              )}
            </Menu.Item>
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={() => handleAction('deploy', 'production')}
                  className={`${
                    active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                  } group flex w-full items-center px-4 py-2 text-sm`}
                >
                  <ArrowUpTrayIcon className="mr-3 h-5 w-5 text-red-400" />
                  Deploy to Production
                </button>
              )}
            </Menu.Item>
            <div className="border-t border-gray-100" />
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={() => handleAction('test')}
                  className={`${
                    active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                  } group flex w-full items-center px-4 py-2 text-sm`}
                >
                  <BeakerIcon className="mr-3 h-5 w-5 text-gray-400" />
                  Run E2E Tests
                </button>
              )}
            </Menu.Item>
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={() => window.location.reload()}
                  className={`${
                    active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                  } group flex w-full items-center px-4 py-2 text-sm`}
                >
                  <ArrowPathIcon className="mr-3 h-5 w-5 text-gray-400" />
                  Refresh Dashboard
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Menu>

      {/* Confirmation Modal */}
      {isConfirmOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto" data-testid="confirm-modal">
          <div className="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
            
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100">
                  <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="mt-3 text-center sm:mt-5">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Confirm Action
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      {pendingAction?.type === 'deploy' && (
                        <>Are you sure you want to deploy to {pendingAction.environment}?</>
                      )}
                      {pendingAction?.type === 'test' && (
                        <>Are you sure you want to run E2E tests?</>
                      )}
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                <button
                  type="button"
                  onClick={confirmAction}
                  disabled={deployMutation.isPending || testMutation.isPending}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm disabled:opacity-50"
                >
                  {(deployMutation.isPending || testMutation.isPending) ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    'Confirm'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsConfirmOpen(false)
                    setPendingAction(null)
                  }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// Missing import
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'