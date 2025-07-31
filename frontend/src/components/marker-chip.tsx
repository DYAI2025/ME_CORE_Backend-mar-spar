"use client";

import { DetectedMarker } from '@/types/analysis';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface MarkerChipProps {
  marker: DetectedMarker;
  onClick?: (marker: DetectedMarker) => void;
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
}

const conceptColors: Record<string, string> = {
  // Emotions
  'fear': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  'anxiety': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  'anger': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  'joy': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  'love': 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  
  // Relational
  'attachment': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  'distance': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
  'conflict': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  
  // Cognitive
  'uncertainty': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  'clarity': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  
  // Default
  'default': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
};

export function MarkerChip({ marker, onClick, size = 'md', showScore = true }: MarkerChipProps) {
  const concept = marker.frame.concept.toLowerCase();
  const colorClass = conceptColors[concept] || conceptColors.default;
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  const score = marker.scoring 
    ? (marker.scoring.base * marker.scoring.weight).toFixed(2)
    : '1.00';

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full transition-all',
        colorClass,
        sizeClasses[size],
        onClick && 'cursor-pointer hover:scale-105 hover:shadow-md',
      )}
      onClick={() => onClick?.(marker)}
    >
      <span className="font-medium">{marker.id}</span>
      {showScore && (
        <Badge variant="secondary" className="text-xs">
          {score}
        </Badge>
      )}
      <span className="text-xs opacity-75">
        {marker.frame.pragmatics}
      </span>
    </div>
  );
}