"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { demoTexts } from '@/lib/demo-texts';
import { Play, Sparkles, FileText, MessageSquare, Mail } from 'lucide-react';

interface DemoModeProps {
  onSelectDemo: (text: string, schemaId: string) => void;
}

export function DemoMode({ onSelectDemo }: DemoModeProps) {
  const [open, setOpen] = useState(false);

  const handleDemoSelect = (demoId: string) => {
    const demo = demoTexts.find(d => d.id === demoId);
    if (demo) {
      // Default to chat schema for demos
      const schemaId = demoId === 'chat' ? 'SCH_relation_analyse_schema' : 'SCH_meta_text_analyse';
      onSelectDemo(demo.content, schemaId);
      setOpen(false);
    }
  };

  const getIcon = (id: string) => {
    switch (id) {
      case 'chat-conflict':
        return <MessageSquare className="w-5 h-5" />;
      case 'email-professional':
        return <Mail className="w-5 h-5" />;
      case 'diary-entry':
        return <FileText className="w-5 h-5" />;
      default:
        return <Sparkles className="w-5 h-5" />;
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Play className="w-4 h-4" />
          Demo starten
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Demo-Texte auswählen</DialogTitle>
          <DialogDescription>
            Wähle einen Beispieltext, um die MarkerEngine in Aktion zu sehen
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          {demoTexts.map((demo) => (
            <Card 
              key={demo.id} 
              className="cursor-pointer transition-all hover:shadow-md hover:scale-[1.02]"
              onClick={() => handleDemoSelect(demo.id)}
            >
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  {getIcon(demo.id)}
                  {demo.title}
                </CardTitle>
                <CardDescription>Demo für {demo.title}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {demo.content.substring(0, 150)}...
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary" className="text-xs">
                      {demo.id === 'chat' ? 'Chat Analyse' : 'Meta-Text-Analyse'}
                    </Badge>
                    {demo.expectedMarkers && demo.expectedMarkers.slice(0, 3).map((marker) => (
                      <Badge key={marker} variant="outline" className="text-xs">
                        {marker}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}