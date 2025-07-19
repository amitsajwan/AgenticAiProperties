"use client";

import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import api from "@/lib/api";

interface AnalyticsData {
  date: string;
  likes: number;
  comments: number;
  shares: number;
  impressions: number;
}

interface InsightsChartProps {
  agentId: string;
}

export default function InsightsChart({ agentId }: InsightsChartProps) {
  const [data, setData] = useState<AnalyticsData[]>([]);


  useEffect(() => {
  api
    .get<AnalyticsData[]>(`/facebook/insights/agents/${agentId}?days=7`)
    .then((res) => {
      const validData = Array.isArray(res) ? res : [];
      setData(validData);
    })
    .catch((err) => {
      console.error("Error fetching analytics:", err);
      setData([]);
    });
}, [agentId]);



  if (data.length === 0) {
    return <p>Loading analytics…</p>;
  }

  return (
    <div className="bg-white p-6 rounded-2xl shadow-md">
      <h2 className="text-xl font-semibold mb-4">Post Performance</h2>
      <ResponsiveContainer width="100%" height={300}>
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
  );
}


