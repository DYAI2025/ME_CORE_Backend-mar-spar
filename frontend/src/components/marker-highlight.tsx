"use client";

import { DetectedMarker } from '@/types';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface MarkerHighlightProps {
  text: string;
  markers: DetectedMarker[];
}

const markerColors = [
  'bg-yellow-200 dark:bg-yellow-900',
  'bg-blue-200 dark:bg-blue-900',
  'bg-green-200 dark:bg-green-900',
  'bg-purple-200 dark:bg-purple-900',
  'bg-pink-200 dark:bg-pink-900',
  'bg-orange-200 dark:bg-orange-900',
];

export function MarkerHighlight({ text, markers }: MarkerHighlightProps) {
  // Extract all position segments from markers and sort them
  const positionSegments = markers
    .filter(m => m.positions && m.positions.length > 0)
    .flatMap(marker => 
      marker.positions.map(pos => ({ ...pos, marker }))
    )
    .sort((a, b) => a.start - b.start);

  if (positionSegments.length === 0) {
    return <p className="whitespace-pre-wrap">{text}</p>;
  }

  const segments: JSX.Element[] = [];
  let lastEnd = 0;

  positionSegments.forEach((segment, index) => {
    const { start, end, marker } = segment;
    
    // Add text before marker
    if (start > lastEnd) {
      segments.push(
        <span key={`text-${lastEnd}`}>
          {text.substring(lastEnd, start)}
        </span>
      );
    }

    // Add highlighted marker text
    const colorClass = markerColors[index % markerColors.length];
    segments.push(
      <TooltipProvider key={`marker-${index}`}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              className={cn(
                'px-1 rounded cursor-help transition-all hover:opacity-80',
                colorClass
              )}
            >
              {text.substring(start, end)}
            </span>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p className="font-semibold">{marker.name}</p>
              <p className="text-sm">{marker.category}</p>
              <p className="text-xs text-gray-500">Confidence: {(marker.confidence * 100).toFixed(1)}%</p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );

    lastEnd = end;
  });

  // Add remaining text
  if (lastEnd < text.length) {
    segments.push(
      <span key={`text-${lastEnd}`}>
        {text.substring(lastEnd)}
      </span>
    );
  }

  return <p className="whitespace-pre-wrap">{segments}</p>;
}