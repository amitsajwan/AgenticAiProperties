import crypto from 'crypto';

export const verifySignature = (req: any) => {
  const signature = req.headers['x-hub-signature-256']?.split('sha256=')[1] || '';
  const expectedSignature = crypto
    .createHmac('sha256', process.env.FB_APP_SECRET || '')
    .update(JSON.stringify(req.body))
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
};

export const processWebhookEvent = (event: any) => {
  const { object, entry } = event;
  
  if (object === 'page') {
    entry.forEach((pageEntry: any) => {
      if (pageEntry.changes) {
        handlePageChange(pageEntry.changes[0]);
      }
      if (pageEntry.messaging) {
        handleMessagingEvent(pageEntry.messaging[0]);
      }
    });
  }
};

const handlePageChange = (change: any) => {
  console.log('Page change:', change);
  // Handle specific change types
};

const handleMessagingEvent = (event: any) => {
  console.log('Messaging event:', event);
  // Handle messaging events
};

