"use client";

import { DetectedMarker } from '@/types/analysis';
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
  // Sort markers by position to handle overlaps
  const sortedMarkers = [...markers]
    .filter(m => m.position)
    .sort((a, b) => a.position!.start - b.position!.start);

  if (sortedMarkers.length === 0) {
    return <p className="whitespace-pre-wrap">{text}</p>;
  }

  const segments: JSX.Element[] = [];
  let lastEnd = 0;

  sortedMarkers.forEach((marker, index) => {
    const { start, end } = marker.position!;
    
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
              <p className="font-semibold">{marker.id}</p>
              <p className="text-sm">{marker.frame.concept}</p>
              <p className="text-xs text-gray-500">{marker.frame.pragmatics}</p>
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