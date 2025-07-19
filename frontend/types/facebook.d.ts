interface FacebookPost {
  id: string;
  message: string;
  created_time: string;
  images?: string[];
  status: 'draft' | 'scheduled' | 'published' | 'failed';
  engagement?: {
    likes: number;
    comments: number;
    shares: number;
    impressions: number;
  };
}

interface FacebookPage {
  id: string;
  name: string;
  access_token: string;
  category?: string;
}

interface FacebookWebhookEvent {
  object: 'page' | 'user';
  entry: Array<{
    id: string;
    time: number;
    changes?: Array<{
      field: string;
      value: any;
    }>;
    messaging?: Array<any>;
  }>;
}

interface FacebookAnalyticsData {
  date: string;
  likes: number;
  comments: number;
  shares: number;
  impressions: number;
  ctr?: number;
}

