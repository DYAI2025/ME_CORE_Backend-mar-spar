'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import Editor from '@monaco-editor/react'

interface Schema {
  id: string
  name: string
  version: string
  fields: number
  updated_at: string
}

interface SchemaViewerProps {
  schemas: Schema[]
}

export function SchemaViewer({ schemas }: SchemaViewerProps) {
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null)
  const [expandedSchemas, setExpandedSchemas] = useState<Set<string>>(new Set())

  const toggleExpanded = (schemaId: string) => {
    const newExpanded = new Set(expandedSchemas)
    if (newExpanded.has(schemaId)) {
      newExpanded.delete(schemaId)
    } else {
      newExpanded.add(schemaId)
    }
    setExpandedSchemas(newExpanded)
  }

  return (
    <div className="space-y-4">
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {schemas.map((schema) => (
            <li key={schema.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <button
                      onClick={() => toggleExpanded(schema.id)}
                      className="mr-3 text-gray-400 hover:text-gray-600"
                    >
                      {expandedSchemas.has(schema.id) ? (
                        <ChevronDownIcon className="h-5 w-5" />
                      ) : (
                        <ChevronRightIcon className="h-5 w-5" />
                      )}
                    </button>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {schema.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        Version {schema.version} • {schema.fields} fields
                      </p>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    Updated {new Date(schema.updated_at).toLocaleDateString()}
                  </div>
                </div>

                {expandedSchemas.has(schema.id) && (
                  <div className="mt-4 ml-8">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-700 mb-2">
                        Schema definition for {schema.name}
                      </p>
                      <button
                        onClick={() => setSelectedSchema(schema.id)}
                        className="text-sm text-primary-600 hover:text-primary-500"
                      >
                        View full schema →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {selectedSchema && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
            
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full sm:p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Schema: {schemas.find(s => s.id === selectedSchema)?.name}
                </h3>
                <button
                  onClick={() => setSelectedSchema(null)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="h-96">
                <Editor
                  height="100%"
                  defaultLanguage="json"
                  value={JSON.stringify(
                    {
                      id: selectedSchema,
                      name: schemas.find(s => s.id === selectedSchema)?.name,
                      version: schemas.find(s => s.id === selectedSchema)?.version,
                      fields: [
                        { name: "id", type: "string", required: true },
                        { name: "type", type: "string", required: true },
                        { name: "keywords", type: "array", items: { type: "string" } },
                        { name: "confidence", type: "number", min: 0, max: 1 }
                      ]
                    },
                    null,
                    2
                  )}
                  theme="vs-light"
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    fontSize: 14,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}