"use client";

import { useEffect, useState } from "react";
import { useRouter } from 'next/navigation'; // [MODIFIED] Import useRouter for redirection

import AgentHeader from "@/components/AgentHeader";
import FacebookConnectCard from "@/components/social/FacebookConnectCard";
import AgentSettingsForm from "@/components/settings/AgentSettingsForm";
// import FacebookPostComposer from "@/components/social/FacebookPostComposer"; // [REMOVED] - No longer needed here
import AiPostGenerator from "@/components/AiPostGenerator";
import BotWidget from "@/components/bot/BotWidget"; // [MODIFIED] - Using the improved BotWidget
import InsightsChart from "@/components/InsightsChart";
import api from "@/lib/api";

interface AgentData {
  name: string;
  description: string;
  // [MODIFIED] - Ensure properties match the actual API response from agent_website.py
  agent_id: string;
  logo_url?: string;
  cover_image_url?: string;
  posts?: string[];
}

interface FacebookStatus {
    access_token_status: 'valid' | 'missing';
    permissions_ok: boolean;
}

export default function AgentPage() {
  const [agent, setAgent] = useState<AgentData | null>(null);
  const [fbStatus, setFbStatus] = useState<FacebookStatus | null>(null);
  const [loading, setLoading] = useState(true);
  
  // A real app would get this from auth context
  const agentId = "test_001"; 

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch agent and Facebook status in parallel
        const [agentRes, statusRes] = await Promise.all([
            api.get<AgentData>(`/agents/${agentId}`),
            api.get<FacebookStatus>(`/facebook/status/agents/${agentId}`)
        ]);
        setAgent(agentRes.data);
        setFbStatus(statusRes.data);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [agentId]);

  const handleConnectionChange = (newStatus: FacebookStatus) => {
    setFbStatus(newStatus);
  }

  if (loading) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        Loading agent dashboard…
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="p-6 text-center text-red-500">
        Could not load agent data. Please try again later.
      </div>
    );
  }

  return (
    <div className="space-y-8 px-4 py-6 max-w-7xl mx-auto">
      {/* Header */}
      <AgentHeader
        name={agent.name}
        businessName={agent.name}
        profileImageUrl={agent.logo_url}
      />

      {/* [MODIFIED] - New Layout: Settings and connection status are grouped */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
            <AgentSettingsForm agentId={agentId} initialSettings={agent} />
        </div>
        <div className="space-y-6">
            <FacebookConnectCard
              agentId={agentId}
              status={fbStatus}
              onConnectionChange={handleConnectionChange}
            />
        </div>
      </div>


      {/* [MODIFIED] - AI Generator now takes up the full width in its section */}
      <div className="grid grid-cols-1 gap-8">
        <AiPostGenerator agentId={agentId} />
      </div>

      {/* Chat Assistant + Insights */}
      <div className="grid md:grid-cols-2 gap-8">
        <BotWidget />
        <InsightsChart agentId={agentId} />
      </div>
    </div>
  );
}

