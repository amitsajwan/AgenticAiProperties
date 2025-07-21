"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useToast } from "@/components/ui/use-toast";

interface AiImageGeneratorProps {
  agentId: string;
  onImageGenerated: (imageUrl: string) => void;
}

export function AiImageGenerator({ agentId, onImageGenerated }: AiImageGeneratorProps) {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();

  const generateImage = async () => {
    if (!prompt.trim()) {
      toast({
        title: "Error",
        description: "Please enter an image description",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    setProgress(10);

    try {
      // Simulate API call - replace with actual API call to your backend
      setProgress(30);
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setProgress(70);
      // This would come from your API response
      const mockImageUrl = `https://source.unsplash.com/random/800x600/?real-estate,${encodeURIComponent(prompt)}`;
      
      setProgress(90);
      onImageGenerated(mockImageUrl);
      
      toast({
        title: "Success",
        description: "Image generated successfully!",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate image",
        variant: "destructive"
      });
    } finally {
      setProgress(100);
      setTimeout(() => setIsLoading(false), 500);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>AI Image Generator</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="image-prompt">Describe the image you need</Label>
          <Input
            id="image-prompt"
            placeholder="e.g., 'Modern luxury condo with city skyline view'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
          />
        </div>

        {isLoading && (
          <div className="space-y-2">
            <Progress value={progress} />
            <p className="text-sm text-muted-foreground">
              Generating image ({progress}%)...
            </p>
          </div>
        )}

        <Button 
          onClick={generateImage}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? "Generating..." : "Generate Image"}
        </Button>
      </CardContent>
    </Card>
  );
}