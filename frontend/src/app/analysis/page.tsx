"use client";

import { useState } from 'react';
import { InputCard } from '@/components/input-card';
import { ResultDisplay } from '@/components/result-display';
import { AnalysisRequest, AnalysisResponse } from '@/types';
import { analyzeText, analyzeChat } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export default function AnalysisPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const { toast } = useToast();

  const handleAnalysis = async (request: AnalysisRequest) => {
    setIsLoading(true);
    try {
      const response = await analyzeText(request);
      setResult(response);
      toast({
        title: "Analyse erfolgreich",
        description: `${response.marker_count} Marker erkannt`,
      });
    } catch (error) {
      toast({
        title: "Fehler bei der Analyse",
        description: error instanceof Error ? error.message : "Ein unbekannter Fehler ist aufgetreten",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight">MarkerEngine Analysis</h1>
          <p className="text-lg text-muted-foreground mt-2">
            Analysieren Sie Texte mit Lean-Deep 3.1 kompatiblen Markern
          </p>
        </div>

        <InputCard
          onAnalyze={handleAnalysis}
          schemas={[
            {
              id: 'SCH_relation_analyse_schema',
              name: 'Chat Analyse',
              description: 'Analyse von Beziehungsdynamiken in Chat-Verläufen',
              version: '1.0.0',
              markers: [],
            },
            {
              id: 'SCH_meta_text_analyse',
              name: 'Meta-Text-Analyse',
              description: 'Übergeordnete Textmuster und Strukturen',
              version: '1.0.0',
              markers: [],
            },
          ]}
          isLoading={isLoading}
        />

        {result && (
          <ResultDisplay
            result={result}
            isLoading={isLoading}
          />
        )}
      </div>
    </div>
  );
}