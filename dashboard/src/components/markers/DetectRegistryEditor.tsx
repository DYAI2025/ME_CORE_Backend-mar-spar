'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import { updateDetectRegistry, validateRegistry } from '@/lib/api'
import toast from 'react-hot-toast'
import { 
  DocumentTextIcon, 
  ArrowUpTrayIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'

interface DetectRegistryEditorProps {
  registry: any
}

export function DetectRegistryEditor({ registry }: DetectRegistryEditorProps) {
  const [editorContent, setEditorContent] = useState(
    JSON.stringify(registry, null, 2)
  )
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const queryClient = useQueryClient()

  const validateMutation = useMutation({
    mutationFn: validateRegistry,
    onSuccess: (result) => {
      if (result.valid) {
        setValidationErrors([])
        toast.success('Registry is valid')
      } else {
        setValidationErrors(result.errors || ['Invalid registry format'])
        toast.error('Registry validation failed')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: updateDetectRegistry,
    onSuccess: () => {
      toast.success('Registry updated successfully')
      queryClient.invalidateQueries({ queryKey: ['detect-registry'] })
      queryClient.invalidateQueries({ queryKey: ['markers'] })
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update registry')
    },
  })

  const handleValidate = () => {
    try {
      const parsed = JSON.parse(editorContent)
      validateMutation.mutate(parsed)
    } catch (error) {
      setValidationErrors(['Invalid JSON format'])
      toast.error('Invalid JSON format')
    }
  }

  const handleSave = () => {
    try {
      const parsed = JSON.parse(editorContent)
      updateMutation.mutate(parsed)
    } catch (error) {
      toast.error('Invalid JSON format')
    }
  }

  const handleRevert = () => {
    setEditorContent(JSON.stringify(registry, null, 2))
    setValidationErrors([])
    toast.success('Reverted to original')
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <DocumentTextIcon className="h-6 w-6 text-gray-400" />
              <h2 className="text-lg font-medium text-gray-900">
                DETECT Registry Editor
              </h2>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleRevert}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Revert
              </button>
              <button
                onClick={handleValidate}
                disabled={validateMutation.isPending}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                {validateMutation.isPending ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
                ) : (
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                )}
                Validate
              </button>
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending || validationErrors.length > 0}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {updateMutation.isPending ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                )}
                Save Changes
              </button>
            </div>
          </div>
        </div>

        {validationErrors.length > 0 && (
          <div className="bg-red-50 border-b border-red-200 px-6 py-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Validation Errors
                </h3>
                <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="p-6">
          <Editor
            height="600px"
            defaultLanguage="json"
            value={editorContent}
            onChange={(value) => setEditorContent(value || '')}
            theme="vs-light"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              formatOnPaste: true,
              formatOnType: true,
              automaticLayout: true,
            }}
          />
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">
          Registry Format Guide
        </h3>
        <p className="text-sm text-blue-700">
          The DETECT registry defines marker detection patterns. Each entry should have:
        </p>
        <ul className="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1">
          <li><code className="bg-blue-100 px-1 rounded">id</code>: Unique marker identifier</li>
          <li><code className="bg-blue-100 px-1 rounded">type</code>: Detection type (keyword, pattern, semantic)</li>
          <li><code className="bg-blue-100 px-1 rounded">keywords</code>: Array of keywords (for keyword type)</li>
          <li><code className="bg-blue-100 px-1 rounded">pattern</code>: Regex pattern (for pattern type)</li>
          <li><code className="bg-blue-100 px-1 rounded">confidence</code>: Detection confidence (0-1)</li>
        </ul>
      </div>
    </div>
  )
}