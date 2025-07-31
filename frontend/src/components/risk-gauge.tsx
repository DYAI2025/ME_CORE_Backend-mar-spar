"use client";

import { cn } from '@/lib/utils';

interface RiskGaugeProps {
  score: number; // 0.0 - 1.0
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function RiskGauge({ score, size = 'md', showLabel = true }: RiskGaugeProps) {
  const percentage = Math.round(score * 100);
  
  // Determine color based on score
  const getColor = (score: number) => {
    if (score < 0.33) return 'text-green-500';
    if (score < 0.66) return 'text-yellow-500';
    return 'text-red-500';
  };
  
  const getRiskLevel = (score: number) => {
    if (score < 0.33) return 'Niedrig';
    if (score < 0.66) return 'Mittel';
    return 'Hoch';
  };

  const sizeConfig = {
    sm: { width: 80, strokeWidth: 6, fontSize: 'text-sm' },
    md: { width: 120, strokeWidth: 8, fontSize: 'text-base' },
    lg: { width: 160, strokeWidth: 10, fontSize: 'text-lg' },
  };

  const config = sizeConfig[size];
  const radius = (config.width - config.strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: config.width, height: config.width }}>
        <svg
          className="transform -rotate-90"
          width={config.width}
          height={config.width}
        >
          {/* Background circle */}
          <circle
            cx={config.width / 2}
            cy={config.width / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={config.strokeWidth}
            fill="none"
            className="text-gray-200 dark:text-gray-700"
          />
          {/* Progress circle */}
          <circle
            cx={config.width / 2}
            cy={config.width / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={config.strokeWidth}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className={cn('transition-all duration-500', getColor(score))}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn('font-bold', config.fontSize, getColor(score))}>
            {percentage}%
          </span>
        </div>
      </div>
      {showLabel && (
        <span className={cn('font-medium', config.fontSize, getColor(score))}>
          Risiko: {getRiskLevel(score)}
        </span>
      )}
    </div>
  );
}