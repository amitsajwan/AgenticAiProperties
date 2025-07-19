// components/social/FacebookPostComposer.tsx
'use client';

import { useState } from 'react';
import { Image, X, Calendar, Send } from 'lucide-react';
import api from '@/lib/api';

interface FacebookPostComposerProps {
  agentId: string;
  pageId?: string;
  accessToken?: string;
  onPostPublished?: (post: any) => void;
}

export default function FacebookPostComposer({
  agentId,
  pageId,
  accessToken,
  onPostPublished,
}: FacebookPostComposerProps) {
  const [caption, setCaption] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [scheduledTime, setScheduledTime] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [postResult, setPostResult] = useState<any>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const filesArray = Array.from(e.target.files);
    const validImages = filesArray.filter((file) => {
      const isValidType = file.type.startsWith('image/');
      const isValidSize = file.size <= 5 * 1024 * 1024;
      if (!isValidType) setStatus('❌ Only image files allowed.');
      if (!isValidSize) setStatus('❌ Each image must be ≤5MB.');
      return isValidType && isValidSize;
    });
    setImages((prev) => [...prev, ...validImages].slice(0, 10));
    setStatus(null);
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handlePostSubmit = async () => {
    if (!caption.trim() && images.length === 0) {
      setStatus('❌ Add a caption or at least one image.');
      return;
    }

    const formData = new FormData();
    formData.append('agent_id', agentId);
    formData.append('caption', caption);
    if (scheduledTime) formData.append('scheduled_time', scheduledTime);
    images.forEach((file) => formData.append('images', file));

    setSubmitting(true);
    setStatus(null);

    try {
      const response = await api.post('/facebook/posts', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const post = response.data;
      console.log('Axios response:', response);
      console.log('Post result:', post);

      setPostResult(post);
      setStatus(
        `✅ Published (ID: ${post.post_id}) — "${post.message}". View at ${post.url}`
      );
      onPostPublished?.(post);

      setCaption('');
      setImages([]);
      setScheduledTime('');
    } catch (err: any) {
      console.error('Error publishing post:', err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'An unknown error occurred.';
      setStatus(`❌ ${msg}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-md">
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">
        Compose Facebook Post
      </h2>

      {/* Caption Input */}
      <textarea
        rows={4}
        maxLength={2000}
        placeholder="What's on your mind?"
        value={caption}
        onChange={(e) => setCaption(e.target.value)}
        className="w-full mb-2 p-3 border rounded-xl resize-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
      />
      <div className="text-right text-sm text-gray-500 mb-4">
        {caption.length}/2000
      </div>

      {/* Image Upload */}
      <label className="flex items-center space-x-2 mb-4 cursor-pointer bg-gray-50 dark:bg-gray-800 p-3 rounded-xl border-2 border-dashed hover:border-blue-500 transition-colors">
        <Image className="h-5 w-5 text-gray-500" />
        <span className="text-gray-600 dark:text-gray-300">Add photos</span>
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleImageChange}
          className="hidden"
        />
      </label>

      {/* Image Previews */}
      {images.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-4">
          {images.map((img, idx) => (
            <div key={idx} className="relative group">
              <img
                src={URL.createObjectURL(img)}
                alt={`preview-${idx}`}
                className="w-full h-24 object-cover rounded-lg"
              />
              <button
                onClick={() => removeImage(idx)}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Schedule Option */}
      <div className="mb-4">
        <label className="flex items-center space-x-2 mb-2">
          <Calendar className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-300">
            Schedule (optional)
          </span>
        </label>
        <input
          type="datetime-local"
          value={scheduledTime}
          onChange={(e) => setScheduledTime(e.target.value)}
          min={new Date().toISOString().slice(0, 16)}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
        />
      </div>

      {/* Submit Button */}
      <button
        onClick={handlePostSubmit}
        disabled={submitting || (!caption.trim() && images.length === 0)}
        className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white py-3 rounded-xl disabled:opacity-50 hover:bg-blue-700 transition-colors"
      >
        <Send className="h-4 w-4" />
        <span>{submitting ? 'Publishing...' : 'Publish Post'}</span>
      </button>

      {/* Status Message */}
      {status && (
        <div className="mt-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
          <p className="text-sm text-gray-700 dark:text-gray-300">{status}</p>
        </div>
      )}

      {/* Full JSON Response */}
      {postResult && (
        <pre className="mt-4 p-3 bg-black text-green-200 rounded overflow-auto text-xs">
          {JSON.stringify(postResult, null, 2)}
        </pre>
      )}
    </div>
  );
}

