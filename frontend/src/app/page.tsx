"use client";

import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { AnalysisRequest, AnalysisResponse, AnalysisSchema } from '@/types/analysis';
import { InputCard } from '@/components/input-card';
import { ResultDisplay } from '@/components/result-display';
import { toast } from 'sonner';

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [schemas] = useState<AnalysisSchema[]>([
    {
      id: 'SCH_relation_analyse_schema',
      name: 'Chat Analyse',
      description: 'Analyse von Beziehungsdynamiken in Chat-Verläufen',
    },
    {
      id: 'SCH_meta_text_analyse',
      name: 'Meta-Text-Analyse',
      description: 'Übergeordnete Textmuster und Strukturen',
    },
  ]);

  const handleAnalyze = useCallback(async (request: AnalysisRequest) => {
    setIsLoading(true);
    setAnalysisResult(null);

    try {
      const result = await api.analyze(request);
      setAnalysisResult(result);
      
      if (result.marker_count === 0) {
        toast.info('Keine Marker gefunden', {
          description: 'Der Text enthält keine erkennbaren Muster für das gewählte Schema.',
        });
      } else {
        toast.success('Analyse abgeschlossen', {
          description: `${result.marker_count} Marker erkannt`,
        });
      }
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error('Fehler bei der Analyse', {
        description: error instanceof Error ? error.message : 'Ein unerwarteter Fehler ist aufgetreten',
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          MarkerEngine
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Entdecke die Bedeutungsschichten deines Textes
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <InputCard
            onAnalyze={handleAnalyze}
            schemas={schemas}
            isLoading={isLoading}
          />
        </div>

        <div className="space-y-6">
          {analysisResult && (
            <ResultDisplay
              result={analysisResult}
              isLoading={isLoading}
            />
          )}
        </div>
      </div>
    </div>
  );
}