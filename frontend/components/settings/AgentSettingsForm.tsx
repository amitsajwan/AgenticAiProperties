'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';

interface AgentSettings {
  agentId: string;
  name: string;
  email: string;
  phone: string;
  bio: string;
}

export default function AgentSettingsForm({ agentId }: { agentId: string }) {
  const [settings, setSettings] = useState<AgentSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await api.get(`/agents/${agentId}/settings`);

        setSettings(res.data);
      } catch (err) {
        console.error('Error fetching settings:', err);
        setStatus('❌ Failed to load settings.');
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, [agentId]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    if (!settings) return;
    setSettings({ ...settings, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    setUpdating(true);
    setStatus(null);
    try {
      const res = await api.patch(`/agents/${agentId}`, settings);

      setSettings(res.data);
      setStatus('✅ Settings updated successfully.');
    } catch (err) {
      console.error('Error updating settings:', err);
      setStatus('❌ An error occurred while updating.');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return <p className="text-gray-500">Loading agent settings...</p>;
  }
  if (!settings) {
    return <p className="text-red-600">❌ Could not load settings.</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Agent Settings</h2>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Name</label>
        <input
          name="name"
          value={settings.name}
          onChange={handleChange}
          className="w-full p-2 border rounded"
          type="text"
        />
      </div>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Email</label>
        <input
          name="email"
          value={settings.email}
          onChange={handleChange}
          className="w-full p-2 border rounded"
          type="email"
        />
      </div>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Phone</label>
        <input
          name="phone"
          value={settings.phone}
          onChange={handleChange}
          className="w-full p-2 border rounded"
          type="tel"
        />
      </div>

      <div className="mb-4">
        <label className="block mb-1 font-medium">Bio</label>
        <textarea
          name="bio"
          value={settings.bio}
          onChange={handleChange}
          className="w-full p-2 border rounded"
          rows={3}
        />
      </div>

      <button
        type="submit"
        disabled={updating}
        className={`px-4 py-2 rounded text-white ${
          updating ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
        }`}
      >
        {updating ? 'Updating...' : 'Update Settings'}
      </button>

      {status && <p className="mt-4 text-sm text-gray-700">{status}</p>}
    </form>
  );
}

