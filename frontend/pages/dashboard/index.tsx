"use client"; // Add this directive at the very top

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import api from '@/lib/api'; // [MODIFIED] Changed to import default export
import AgentSettingsForm from '@/components/settings/AgentSettingsForm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ReloadIcon } from '@radix-ui/react-icons';

interface AgentWebsite {
  agent_id: string;
  name: string;
  description?: string;
  logo_url?: string;
  cover_image_url?: string;
  posts: any[];
}

interface FacebookStatus {
  has_user_token: boolean;
  has_page_token: boolean;
  has_required_permissions: boolean;
  page_name?: string;
  page_id?: string;
}

interface AnalyticsData {
  total_posts: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_impressions: number;
}

const AgentPage: React.FC = () => {
  const router = useRouter();
  const { agent_id } = router.query;

  const [agentData, setAgentData] = useState<AgentWebsite | null>(null);
  const [facebookStatus, setFacebookStatus] = useState<FacebookStatus | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loadingAgentData, setLoadingAgentData] = useState(true);
  const [loadingFacebookStatus, setLoadingFacebookStatus] = useState(true);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgentData = useCallback(async () => {
    if (!agent_id) return;
    setLoadingAgentData(true);
    setError(null);
    try {
      const response = await api.get<AgentWebsite>(`/agents/${agent_id}`);
      setAgentData(response.data);
    } catch (err: any) {
      console.error('Failed to load agent data:', err);
      setError(err.response?.data?.detail || 'Failed to load agent data. Please ensure the agent exists and try again later.');
    } finally {
      setLoadingAgentData(false);
    }
  }, [agent_id]);

  const fetchFacebookStatus = useCallback(async () => {
    if (!agent_id) return;
    setLoadingFacebookStatus(true);
    try {
      const response = await api.get<FacebookStatus>(`/facebook/status/check/${agent_id}`);
      setFacebookStatus(response.data);
    } catch (err) {
      console.error('Failed to load Facebook status:', err);
      setFacebookStatus(null);
    } finally {
      setLoadingFacebookStatus(false);
    }
  }, [agent_id]);

  const fetchAnalyticsData = useCallback(async () => {
    if (!agent_id) return;
    setLoadingAnalytics(true);
    try {
      const response = await api.get<AnalyticsData>(`/facebook/insights/agents/${agent_id}?days=7`);
      setAnalyticsData(response.data);
    } catch (err) {
      console.error('Failed to load analytics data:', err);
      setAnalyticsData(null);
    } finally {
      setLoadingAnalytics(false);
    }
  }, [agent_id]);

  const refreshAllData = useCallback(() => {
    fetchAgentData();
    fetchFacebookStatus();
    fetchAnalyticsData();
  }, [fetchAgentData, fetchFacebookStatus, fetchAnalyticsData]);

  useEffect(() => {
    refreshAllData();
  }, [refreshAllData]);

  const handleFacebookLogin = () => {
    if (agent_id) {
      window.location.href = `http://localhost:8000/api/facebook/auth/login?agent_id=${agent_id}`;
    }
  };

  if (loadingAgentData && loadingFacebookStatus && loadingAnalytics) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <ReloadIcon className="mr-2 h-8 w-8 animate-spin text-blue-500" />
        <span className="text-lg text-gray-700">Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <Card className="p-6 rounded-xl shadow-lg bg-white text-center">
          <CardTitle className="text-red-600 text-xl mb-4">Error Loading Dashboard</CardTitle>
          <CardContent>
            <p className="text-gray-700">{error}</p>
            <Button onClick={refreshAllData} className="mt-4 bg-blue-600 hover:bg-blue-700 text-white">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!agentData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <Card className="p-6 rounded-xl shadow-lg bg-white text-center">
          <CardTitle className="text-gray-800 text-xl mb-4">Agent Not Found</CardTitle>
          <CardContent>
            <p className="text-gray-700">No data found for agent ID: {agent_id}.</p>
            <p className="text-gray-700">Please ensure the agent exists or create a new one.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isFacebookConnected = facebookStatus?.has_user_token && facebookStatus?.has_page_token && facebookStatus?.has_required_permissions;

  return (
    <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-extrabold text-gray-900 mb-8 text-center">
        Agent Dashboard: {agentData.name}
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card className="h-full rounded-xl shadow-md p-6 bg-white">
            <CardHeader>
              <CardTitle className="text-2xl font-semibold text-gray-800">AI Real Estate Post Generator</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                This section will contain the AI-powered post generation interface.
                (e.g., input for property details, buttons for generating content and images, and a preview area).
              </p>
              <p className="text-gray-500 mt-4">
                *Coming Soon: Fully interactive AI post generation!*
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-1 space-y-8">
          <Card className="rounded-xl shadow-md p-6 bg-white">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-gray-800">Facebook Integration</CardTitle>
            </CardHeader>
            <CardContent>
              {loadingFacebookStatus ? (
                <div className="flex items-center text-blue-500">
                  <ReloadIcon className="mr-2 h-4 w-4 animate-spin" /> Checking status...
                </div>
              ) : (
                <>
                  {isFacebookConnected ? (
                    <div className="text-green-600 font-medium">
                      <p>✅ Connected & Ready!</p>
                      {facebookStatus?.page_name && (
                        <p className="text-sm text-gray-700">Page: {facebookStatus.page_name}</p>
                      )}
                    </div>
                  ) : (
                    <div className="text-red-600 font-medium">
                      <p>❌ Not Connected</p>
                      <Button 
                        onClick={handleFacebookLogin} 
                        className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Connect Facebook
                      </Button>
                    </div>
                  )}
                  <Button 
                    onClick={fetchFacebookStatus} 
                    variant="outline" 
                    size="sm" 
                    className="mt-4 w-full text-blue-600 border-blue-300 hover:bg-blue-50"
                  >
                    Refresh Status
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          <AgentSettingsForm agentData={agentData} refreshAgentData={refreshAllData} />

          <Card className="rounded-xl shadow-md p-6 bg-white">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-gray-800">Post Analytics (Last 7 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              {loadingAnalytics ? (
                <div className="flex items-center text-blue-500">
                  <ReloadIcon className="mr-2 h-4 w-4 animate-spin" /> Loading analytics...
                </div>
              ) : analyticsData && analyticsData.total_posts > 0 ? (
                <div className="space-y-2 text-gray-700">
                  <p><strong>Total Posts:</strong> {analyticsData.total_posts}</p>
                  <p><strong>Total Likes:</strong> {analyticsData.total_likes}</p>
                  <p><strong>Total Comments:</strong> {analyticsData.total_comments}</p>
                  <p><strong>Total Shares:</strong> {analyticsData.total_shares}</p>
                  <p><strong>Total Impressions:</strong> {analyticsData.total_impressions}</p>
                </div>
              ) : (
                <p className="text-gray-500">No analytics data available yet. Publish some posts!</p>
              )}
              <Button 
                onClick={fetchAnalyticsData} 
                variant="outline" 
                size="sm" 
                className="mt-4 w-full text-blue-600 border-blue-300 hover:bg-blue-50"
              >
                Refresh Analytics
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AgentPage;
