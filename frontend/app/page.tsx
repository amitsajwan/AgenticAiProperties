"use client";

import { useState } from "react";
import BotWidget from "../components/BotWidget";
import AgentHeader from "../components/AgentHeader";
import { AiBrandingGenerator } from "../components/AiBrandingGenerator";

export default function HomePage() {
  const [branding, setBranding] = useState<{
    colorScheme?: string;
    tagline?: string;
    logoUrl?: string;
    aiGenerated?: boolean;
  }>({});

  return (
    <main className="min-h-screen">
      {/* Dynamic Banner */}
      <div className={`w-full h-64 ${branding.colorScheme || 'bg-gradient-to-r from-blue-600 to-indigo-800'} 
        flex items-center justify-center text-white`}>
        <div className="text-center max-w-2xl px-4">
          <h1 className="text-4xl font-bold mb-4">
            {branding.tagline || "AI-Powered Real Estate Marketing"}
          </h1>
          <p className="text-xl opacity-90">
            Generate stunning content, branding, and social media posts in seconds
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12 -mt-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 space-y-8">
            <AgentHeader 
              name="Your Agent"
              profileImageUrl={branding.logoUrl}
              businessName={branding.aiGenerated ? "AI Branded Realty" : undefined}
              branding={branding}
            />
            <BotWidget />
          </div>
          
          <div className="md:col-span-1 space-y-8">
            <AiBrandingGenerator 
              agentId="default"
              onBrandingGenerated={(newBranding) => setBranding({
                ...newBranding,
                aiGenerated: true
              })}
            />
          </div>
        </div>
      </div>
    </main>
  );
}
