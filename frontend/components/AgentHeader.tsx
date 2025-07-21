"use client";

import React from "react";

interface AgentHeaderProps {
  name: string;
  profileImageUrl?: string;
  businessName?: string;
  branding?: {
    colorScheme?: string;
    tagline?: string;
    logoUrl?: string;
    aiGenerated?: boolean;
  };
}

export default function AgentHeader({
  name,
  profileImageUrl,
  businessName,
  branding
}: AgentHeaderProps) {
  const logoSrc = branding?.logoUrl || profileImageUrl;

  return (
    <div className={`flex items-center justify-between p-6 rounded-2xl shadow-md 
      ${branding?.colorScheme || 'bg-gradient-to-r from-blue-500 to-purple-600'}`}>
      <div className="flex items-center space-x-4">
        {logoSrc ? (
          <img
            src={logoSrc}
            alt={name}
            className="h-16 w-16 rounded-full object-cover border-4 border-white/80"
          />
        ) : (
          <div className="h-16 w-16 rounded-full bg-white/20 backdrop-blur-sm" />
        )}
        <div>
          <h1 className="text-2xl font-bold text-white">
            {businessName || name}
          </h1>
          {branding?.tagline && (
            <p className="text-sm text-white/90">{branding.tagline}</p>
          )}
          {branding?.aiGenerated && (
            <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-white/20 rounded-full text-white">
              AI Branding
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center space-x-2 bg-white/20 px-3 py-1 rounded-full">
        <span className="inline-block w-3 h-3 rounded-full bg-green-400 animate-pulse" />
        <p className="text-sm text-white">Online</p>
      </div>
    </div>
  );
}
