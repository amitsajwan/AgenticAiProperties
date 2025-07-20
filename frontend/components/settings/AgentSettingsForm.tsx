import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { ReloadIcon } from '@radix-ui/react-icons';
import api from '@/lib/api'; 

// Define the AgentWebsite type based on your backend model
interface AgentWebsite {
  agent_id: string;
  name: string;
  description?: string;
  logo_url?: string; // This should now be just the filename, e.g., "amit_logo.png"
  cover_image_url?: string;
  posts: any[];
}

interface AgentSettingsFormProps {
  agentData: AgentWebsite;
  refreshAgentData: () => void;
}

const AgentSettingsForm: React.FC<AgentSettingsFormProps> = ({ agentData, refreshAgentData }) => {
  const [agentName, setAgentName] = useState(agentData.name);
  const [agentDescription, setAgentDescription] = useState(agentData.description || '');
  const [logoPrompt, setLogoPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    setAgentName(agentData.name);
    setAgentDescription(agentData.description || '');
  }, [agentData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const updates: { name: string; description: string; logo_prompt?: string } = {
        name: agentName,
        description: agentDescription,
      };

      if (logoPrompt.trim()) {
        updates.logo_prompt = logoPrompt.trim();
      }

      const response = await api.patch(`/agents/${agentData.agent_id}`, updates);
      console.log('Branding updated successfully:', response.data);
      setSuccessMessage('Branding updated successfully! Website is regenerating...');
      
      refreshAgentData(); 
      
      setLogoPrompt('');

    } catch (err: any) {
      console.error('Failed to update branding:', err);
      setError(err.response?.data?.detail || 'Failed to update branding. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to determine the correct logo source URL
  const getLogoSrc = (logoUrl?: string) => {
    if (!logoUrl) return '';
    // Check if it's a full external URL (e.g., from placehold.co)
    if (logoUrl.startsWith('http://') || logoUrl.startsWith('https://')) {
      return logoUrl;
    }
    // [MODIFIED] Explicitly point to the backend's port for locally generated images
    return `http://localhost:8000/generated_images/${logoUrl}`; 
  };

  return (
    <Card className="w-full max-w-md mx-auto rounded-xl shadow-lg">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-gray-800">Agent Branding Settings</CardTitle>
        <CardDescription className="text-gray-600">
          Customize your agent's name, description, and generate a new logo.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-2">
            <Label htmlFor="agentName" className="text-gray-700">Agent Name</Label>
            <Input
              id="agentName"
              type="text"
              placeholder="Your Agent Name"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              required
              className="rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="agentDescription" className="text-gray-700">Description</Label>
            <Textarea
              id="agentDescription"
              placeholder="A brief description of your real estate services."
              value={agentDescription}
              onChange={(e) => setAgentDescription(e.target.value)}
              rows={4}
              className="rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="logoPrompt" className="text-gray-700">Generate New Logo (AI Prompt)</Label>
            <Input
              id="logoPrompt"
              type="text"
              placeholder="e.g., 'A modern house logo with a tree, in blue and green colors'"
              value={logoPrompt}
              onChange={(e) => setLogoPrompt(e.target.value)}
              className="rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">
              Describe the logo you want. Leave blank to keep current logo.
            </p>
          </div>

          {agentData.logo_url && (
            <div className="grid gap-2">
              <Label className="text-gray-700">Current Logo Preview</Label>
              <img 
                src={getLogoSrc(agentData.logo_url)} 
                alt="Current Agent Logo" 
                className="w-24 h-24 rounded-full object-cover border-2 border-gray-200"
              />
              <p className="text-sm text-gray-500">
                Path: <code>{agentData.logo_url}</code>
              </p>
            </div>
          )}

          {error && (
            <div className="text-red-500 text-sm mt-2 p-3 bg-red-50 rounded-md border border-red-200">
              {error}
            </div>
          )}

          {successMessage && (
            <div className="text-green-600 text-sm mt-2 p-3 bg-green-50 rounded-md border border-green-200">
              {successMessage}
            </div>
          )}

          <Button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md transition-colors duration-200 flex items-center justify-center"
            disabled={isLoading}
          >
            {isLoading && <ReloadIcon className="mr-2 h-4 w-4 animate-spin" />}
            {isLoading ? 'Saving...' : 'Save Branding'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default AgentSettingsForm;
