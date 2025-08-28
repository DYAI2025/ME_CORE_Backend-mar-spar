"use client";

import { useState, useCallback, ChangeEvent } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AnalysisRequest, AnalysisSchema } from '@/types';
import { Upload, FileText, AlertCircle, Sparkles, Trash2 } from 'lucide-react';
import { DemoMode } from './demo-mode';

interface InputCardProps {
  onAnalyze: (request: AnalysisRequest) => void;
  schemas: AnalysisSchema[];
  isLoading?: boolean;
  maxCharacters?: number;
}

export function InputCard({ onAnalyze, schemas, isLoading = false, maxCharacters = 4000 }: InputCardProps) {
  const [text, setText] = useState('');
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);

  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    if (newText.length <= maxCharacters) {
      setText(newText);
    }
  };

  const handleSubmit = () => {
    if (!text.trim() || !selectedSchema) return;

    onAnalyze({
      text: text.trim(),
      schemaId: selectedSchema,
    });
  };

  const handleClear = () => {
    setText('');
  };

  const processFile = useCallback(async (file: File) => {
    try {
      const content = await file.text();
      setText(content.slice(0, maxCharacters));
    } catch (error) {
      console.error('Error reading file:', error);
    }
  }, [maxCharacters]);

  const handleDemoSelect = (demoText: string, schemaId: string) => {
    setText(demoText);
    setSelectedSchema(schemaId);
  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        processFile(acceptedFiles[0]);
      }
      setIsDragging(false);
    },
    onDragEnter: () => setIsDragging(true),
    onDragLeave: () => setIsDragging(false),
    accept: {
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/rtf': ['.rtf'],
    },
    multiple: false,
    noClick: true,
  });

  const isValid = text.trim().length > 0 && selectedSchema;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Text-Eingabe
            </CardTitle>
            <CardDescription>
              Gib einen Text ein oder lade eine Datei hoch (max. {maxCharacters} Zeichen)
            </CardDescription>
          </div>
          <DemoMode onSelectDemo={handleDemoSelect} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Disclaimer */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Hinweis:</strong> Die MarkerEngine bietet eine Perspektiv-Analyse, keine Diagnose. 
            Wir bieten keine therapeutischen oder medizinischen Dienstleistungen an. 
            Bei psychischen Problemen suche bitte professionelle Hilfe.
          </AlertDescription>
        </Alert>

        {/* Text Input with Drag & Drop */}
        <div
          {...getRootProps()}
          className={`relative transition-all ${isDragging ? 'ring-2 ring-blue-500 ring-offset-2' : ''}`}
        >
          <input {...getInputProps()} />
          <Textarea
            value={text}
            onChange={handleTextChange}
            placeholder="Gib hier bitte einen Text deiner Wahl ein. Es kann ein Teil eines Chatverlaufs sein, oder eine E-Mail. Die MarkerEngine wird daraufhin die Bedeutungsschichten dieses Textes aufdecken."
            className="min-h-[300px] resize-none"
            disabled={isLoading}
          />
          
          {/* Character Counter */}
          <div className="absolute bottom-2 right-2 text-sm text-gray-500">
            {text.length} / {maxCharacters}
          </div>

          {/* Drag Overlay */}
          {isDragging && (
            <div className="absolute inset-0 bg-blue-50/90 dark:bg-blue-950/90 flex items-center justify-center rounded-md">
              <div className="text-center">
                <Upload className="w-12 h-12 mx-auto mb-2 text-blue-600" />
                <p className="text-blue-600 font-medium">Datei hier ablegen</p>
                <p className="text-sm text-blue-500">Unterstützt: .txt, .md, .rtf</p>
              </div>
            </div>
          )}
        </div>

        {/* File Upload Button */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => document.getElementById('file-upload')?.click()}
            disabled={isLoading}
          >
            <Upload className="w-4 h-4 mr-2" />
            Datei auswählen
          </Button>
          <input
            id="file-upload"
            type="file"
            accept=".txt,.md,.rtf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) processFile(file);
            }}
          />
          <span className="text-sm text-gray-500">
            oder per Drag & Drop auf das Textfeld ziehen
          </span>
        </div>

        {/* Schema Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Analyse-Schema</label>
          <Select value={selectedSchema} onValueChange={setSelectedSchema} disabled={isLoading}>
            <SelectTrigger>
              <SelectValue placeholder="Wähle ein Analyse-Schema" />
            </SelectTrigger>
            <SelectContent>
              {schemas.map((schema) => (
                <SelectItem key={schema.id} value={schema.id}>
                  <div>
                    <div className="font-medium">{schema.name}</div>
                    {schema.description && (
                      <div className="text-sm text-gray-500">{schema.description}</div>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isLoading}
            className="flex-1"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            {selectedSchema === 'SCH_relation_analyse_schema' ? 'Chat Analyse' : 'Meta-Text-Analyse'}
          </Button>
          <Button
            variant="outline"
            onClick={handleClear}
            disabled={!text || isLoading}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Löschen
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}