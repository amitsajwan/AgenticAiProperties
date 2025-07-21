"use client";

import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner'; // ✅ use sonner for clean toast

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface AiBrandingGeneratorProps {
  agentId: string;
  onBrandingGenerated: (branding: {
    colorScheme: string;
    tagline: string;
    logoUrl: string;
    logoPrompt: string;
  }) => void;
}

export function AiBrandingGenerator({ agentId, onBrandingGenerated }: AiBrandingGeneratorProps) {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const generateBranding = async () => {
    if (!prompt.trim()) {
      toast.error("Please enter a branding description");
      return;
    }

    setIsLoading(true);
    setProgress(10);

    try {
      // 1. Send branding update request
      setProgress(30);
      await axios.patch(`/api/agents/${agentId}`, {
        logo_prompt: prompt,
        tagline: `Your ${prompt.split(' ')[0]} real estate expert`,
        color_scheme: "bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"
      });

      // 2. Get updated branding info
      setProgress(60);
      const res = await axios.get(`/api/agents/${agentId}`);
      const brandingData = res.data;

      // 3. Pass branding info to parent
      setProgress(90);
      onBrandingGenerated({
        colorScheme: brandingData.color_scheme,
        tagline: brandingData.tagline,
        logoUrl: brandingData.logo_url,
        logoPrompt: brandingData.logo_prompt
      });

      toast.success("Branding generated successfully!");
    } catch (error) {
      console.error("Branding generation failed:", error);
      toast.error("Failed to generate branding");
    } finally {
      setProgress(100);
      setTimeout(() => setIsLoading(false), 500);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>AI Branding Generator</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="branding-prompt">Describe your desired branding</Label>
          <Textarea
            id="branding-prompt"
            placeholder="e.g., 'Modern real estate branding with blue tones, professional but approachable'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            disabled={isLoading}
          />
        </div>

        {isLoading && (
          <div className="space-y-2">
            <Progress value={progress} />
            <p className="text-sm text-muted-foreground">
              Generating branding assets ({progress}%)...
            </p>
          </div>
        )}

        <Button 
          onClick={generateBranding}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? "Generating..." : "Generate Branding"}
        </Button>
      </CardContent>
    </Card>
  );
}
