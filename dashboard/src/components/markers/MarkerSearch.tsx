'use client'

import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'

interface MarkerSearchProps {
  value: string
  onChange: (value: string) => void
}

export function MarkerSearch({ value, onChange }: MarkerSearchProps) {
  return (
    <div className="relative">
      <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
        <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="block w-full rounded-md border-gray-300 pl-10 pr-3 py-2 text-sm placeholder-gray-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        placeholder="Search markers..."
        data-testid="marker-search"
      />
    </div>
  )
}