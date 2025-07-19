import { useState } from 'react';
import api from '@/lib/api';

export default function FacebookWebhookSetup({ agentId }: { agentId: string }) {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      await api.post('/facebook/webhooks/subscribe', { agentId });
      setIsSubscribed(true);
    } catch (error) {
      console.error('Subscription failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Webhook Configuration</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Webhook URL
          </label>
          <input
            type="text"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="https://yourdomain.com/api/webhooks/facebook"
          />
        </div>
        
        <button
          onClick={handleSubscribe}
          disabled={loading || isSubscribed}
          className={`px-4 py-2 rounded text-white ${isSubscribed ? 'bg-green-500' : 'bg-blue-500 hover:bg-blue-600'}`}
        >
          {loading ? 'Processing...' : isSubscribed ? 'Subscribed' : 'Subscribe to Webhooks'}
        </button>
        
        {isSubscribed && (
          <p className="text-sm text-green-600">
            Webhook successfully subscribed! You'll now receive real-time updates.
          </p>
        )}
      </div>
    </div>
  );
}

