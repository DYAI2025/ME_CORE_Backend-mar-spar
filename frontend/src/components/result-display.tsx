"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { AnalysisResponse, DetectedMarker } from '@/types/analysis';
import { Brain, Zap, MessageSquare, Activity } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { MarkerHighlight } from './marker-highlight';
import { MarkerChip } from './marker-chip';
import { RiskGauge } from './risk-gauge';

interface ResultDisplayProps {
  result: AnalysisResponse;
  isLoading?: boolean;
}

export function ResultDisplay({ result, isLoading = false }: ResultDisplayProps) {
  const riskScore = Math.min(result.total_score / 10, 1); // Normalize to 0-1

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Analyse-Ergebnis
          </CardTitle>
          <CardDescription>
            {result.marker_count} Marker erkannt • Verarbeitet mit {result.model_used || 'Standard-Engine'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Risk Score */}
            <div className="flex flex-col items-center">
              <RiskGauge score={riskScore} size="lg" />
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Gesamt-Score: {result.total_score.toFixed(2)}
              </p>
            </div>

            {/* Quick Stats */}
            <div className="space-y-3 md:col-span-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Marker erkannt</span>
                <Badge variant="secondary">{result.marker_count}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Verarbeitungszeit</span>
                <Badge variant="outline">
                  {result.processing_time ? `${(result.processing_time * 1000).toFixed(0)}ms` : 'N/A'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">KI-Modell</span>
                <Badge variant="outline">{result.model_used || 'Standard'}</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Results Tabs */}
      <Tabs defaultValue="interpretation" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="interpretation" className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Interpretation
          </TabsTrigger>
          <TabsTrigger value="markers" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Marker
          </TabsTrigger>
          <TabsTrigger value="visualization" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Visualisierung
          </TabsTrigger>
        </TabsList>

        {/* Interpretation Tab */}
        <TabsContent value="interpretation">
          <Card>
            <CardHeader>
              <CardTitle>Narrative Interpretation</CardTitle>
              <CardDescription>
                KI-generierte Analyse der erkannten Muster
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{result.interpretation}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Markers Tab */}
        <TabsContent value="markers">
          <Card>
            <CardHeader>
              <CardTitle>Erkannte Marker</CardTitle>
              <CardDescription>
                Detaillierte Auflistung aller gefundenen Marker
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {result.markers.map((marker, index) => (
                  <MarkerChip
                    key={`${marker.id}-${index}`}
                    marker={marker}
                    onClick={() => {
                      // TODO: Show detailed marker info
                      console.log('Marker clicked:', marker);
                    }}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Visualization Tab */}
        <TabsContent value="visualization">
          <Card>
            <CardHeader>
              <CardTitle>Marker-Verteilung</CardTitle>
              <CardDescription>
                Visuelle Darstellung der Analyse-Ergebnisse
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Marker Categories */}
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Kategorien</h4>
                  {Object.entries(
                    result.markers.reduce((acc, marker) => {
                      const concept = marker.frame.concept;
                      acc[concept] = (acc[concept] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([concept, count]) => (
                    <div key={concept} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>{concept}</span>
                        <span className="text-gray-500">{count}</span>
                      </div>
                      <Progress value={(count / result.marker_count) * 100} className="h-2" />
                    </div>
                  ))}
                </div>

                {/* Placeholder for future graphs */}
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 text-center">
                  <Activity className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-500">
                    Erweiterte Visualisierungen werden in Kürze verfügbar sein
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}