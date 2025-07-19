import React, { useState, FormEvent, ChangeEvent } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Progress } from '@/components/ui/progress';

import FacebookPostComposer from './FacebookPostComposer';

interface AiPostGeneratorProps {
  agentId: string;
}

const parseBrandSuggestions = (suggestionsString: string): string[] => {
  if (!suggestionsString) return [];
  return suggestionsString.split('\n').map(s => s.trim()).filter(s => s.length > 0);
};

const AiPostGenerator: React.FC<AiPostGeneratorProps> = ({ agentId }) => {
  const [prompt, setPrompt] = useState('');
  const [generatedCaption, setGeneratedCaption] = useState('');
  const [generatedImage, setGeneratedImage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);

  const [step, setStep] = useState<'initial' | 'branding_suggestions' | 'post_generation'>('initial');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [brandSuggestions, setBrandSuggestions] = useState<string | null>(null);
  const [parsedSuggestions, setParsedSuggestions] = useState<string[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);

  const resetState = () => {
    setPrompt('');
    setGeneratedCaption('');
    setGeneratedImage('');
    setIsLoading(false);
    setError(null);
    setSuccessMessage(null);
    setProgress(0);
    setStep('initial');
    setSessionId(null);
    setBrandSuggestions(null);
    setParsedSuggestions([]);
    setSelectedBrand(null);
  };

  const handleGenerateBranding = async (e: FormEvent) => {
    e.preventDefault();
    if (!prompt) {
      setError('Please enter a prompt.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    setProgress(20);

    try {
      const response = await axios.post('/api/bot/generate-branding', {
        agent_id: agentId,
        prompt
      });

      setSessionId(response.data.session_id);
      setBrandSuggestions(response.data.brand_suggestions);
      setParsedSuggestions(parseBrandSuggestions(response.data.brand_suggestions));
      setStep('branding_suggestions');
      setProgress(50);
      setSuccessMessage('Brand suggestions generated successfully! Please select one to continue.');
    } catch (err: any) {
      console.error('Error generating branding:', err);
      setError(err.response?.data?.detail || 'Failed to generate brand suggestions.');
      setProgress(0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectBrandAndContinue = async () => {
    if (!sessionId || !selectedBrand) {
      setError('Please select a brand and ensure session is active.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    setProgress(70);

    try {
      const response = await axios.post('/api/bot/continue-post-generation', {
        session_id: sessionId,
        selected_brand: selectedBrand
      });

      setGeneratedCaption(response.data.caption);
      setGeneratedImage(response.data.image_path);
      setStep('post_generation');
      setProgress(100);
      setSuccessMessage('Post content generated successfully! Ready for review and posting.');
    } catch (err: any) {
      console.error('Error continuing post generation:', err);
      setError(err.response?.data?.detail || 'Failed to generate post content.');
      setProgress(0);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto my-8">
      <CardHeader>
        <CardTitle>AI Real Estate Post Generator</CardTitle>
        <CardDescription>Generate captivating social media posts with AI assistance.</CardDescription>
      </CardHeader>
      <CardContent>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        {successMessage && <p className="text-green-500 mb-4">{successMessage}</p>}

        {isLoading && (
          <div className="mb-4">
            <p>Generating content...</p>
            <Progress value={progress} className="w-full" />
          </div>
        )}

        {step === 'initial' && (
          <form onSubmit={handleGenerateBranding} className="space-y-4">
            <div>
              <Label htmlFor="prompt">What kind of property post do you need?</Label>
              <Textarea
                id="prompt"
                placeholder="e.g., 'Luxury downtown condo, 2 beds, great views. Generate branding ideas and a post.'"
                value={prompt}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                rows={4}
                required
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              Generate Branding Ideas
            </Button>
          </form>
        )}

        {step === 'branding_suggestions' && parsedSuggestions.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Select a Brand Suggestion:</h3>
            <RadioGroup
              onValueChange={setSelectedBrand}
              value={selectedBrand || ''}
              className="space-y-2"
              disabled={isLoading}
            >
              {parsedSuggestions.map((suggestion, index) => (
                <div key={index} className="flex items-center space-x-2 border p-3 rounded-md">
                  <RadioGroupItem value={suggestion} id={`brand-${index}`} />
                  <Label htmlFor={`brand-${index}`}>{suggestion}</Label>
                </div>
              ))}
            </RadioGroup>
            <Button
              onClick={handleSelectBrandAndContinue}
              className="w-full"
              disabled={isLoading || !selectedBrand}
            >
              Continue with Selected Brand
            </Button>
            <Button variant="outline" onClick={resetState} className="w-full mt-2" disabled={isLoading}>
              Start Over
            </Button>
          </div>
        )}

        {step === 'post_generation' && generatedCaption && generatedImage && (
          <FacebookPostComposer
            agentId={agentId}
            initialCaption={generatedCaption}
            initialImage={generatedImage}
            onPostSuccess={() => {
              setSuccessMessage('Post successfully published to Facebook!');
              resetState();
            }}
            onPostError={(msg) => setError(`Error publishing post: ${msg}`)}
            onReset={resetState}
          />
        )}

        {step === 'post_generation' && (!generatedCaption || !generatedImage) && !isLoading && (
          <p className="text-red-500">Error: No content generated. Please try again or start over.</p>
        )}
      </CardContent>
      <CardFooter>
        <p className="text-sm text-gray-500">
          Powered by AI. Ensure to review content before publishing.
        </p>
      </CardFooter>
    </Card>
  );
};

export default AiPostGenerator;

