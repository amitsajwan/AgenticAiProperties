import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '@/lib/api';

interface AnalyticsData {
  date: string;
  likes: number;
  comments: number;
  shares: number;
  impressions: number;
}

export default function FacebookAnalytics({ agentId }: { agentId: string }) {
  const [data, setData] = useState<AnalyticsData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get(`/facebook/insights/agents/${agentId}?days=7`);
        setData(response.data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [agentId]);

  if (loading) return <div>Loading analytics...</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Post Performance</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="likes" stroke="#8884d8" />
            <Line type="monotone" dataKey="comments" stroke="#82ca9d" />
            <Line type="monotone" dataKey="shares" stroke="#ffc658" />
            <Line type="monotone" dataKey="impressions" stroke="#ff8042" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

