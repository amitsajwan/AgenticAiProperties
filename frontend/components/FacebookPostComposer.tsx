import React, { useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';

interface FacebookPostComposerProps {
  agentId: string;
  initialCaption: string;
  initialImage: string; // This will be a URL or path to the image
  onPostSuccess: () => void;
  onPostError: (message: string) => void;
  onReset: () => void; // Callback to reset the entire AI generation flow
}

// Helper function to parse detailed error messages from FastAPI/Pydantic
const parseBackendError = (errorResponse: any): string => {
  if (errorResponse && errorResponse.detail) {
    if (Array.isArray(errorResponse.detail)) {
      // It's a list of Pydantic validation errors
      return errorResponse.detail.map((err: any) => {
        const loc = err.loc ? `(${err.loc.join('.')})` : '';
        return `${err.msg} ${loc}`;
      }).join('; ');
    } else if (typeof errorResponse.detail === 'string') {
      // It's a simple string error message
      return errorResponse.detail;
    }
  }
  return 'An unexpected error occurred.';
};


const FacebookPostComposer: React.FC<FacebookPostComposerProps> = ({
  agentId,
  initialCaption,
  initialImage,
  onPostSuccess,
  onPostError,
  onReset,
}) => {
  const [caption, setCaption] = useState<string>(initialCaption);
  const [imagePath, setImagePath] = useState<string>(initialImage);
  const [isPosting, setIsPosting] = useState<boolean>(false);
  const [postError, setPostError] = useState<string | null>(null);
  const [postSuccess, setPostSuccess] = useState<string | null>(null);

  const handlePostToFacebook = async () => {
    setIsPosting(true);
    setPostError(null);
    setPostSuccess(null);

    try {
      // This is the actual call to your backend's Facebook posting endpoint.
      // Assuming /api/facebook/posts exists and expects agent_id, caption, images array
      const response = await axios.post('/api/facebook/posts', {
        agent_id: agentId,
        caption: caption,
        images: [imagePath].filter(Boolean), // Ensure only non-null/non-empty image paths are sent
      });

      if (response.data.status === 'success') {
        setPostSuccess('Post published successfully!');
        onPostSuccess(); // Notify parent component (AiPostGenerator)
      } else {
        // If backend sends a custom error object for non-2xx statuses
        const errorMessage = response.data.message || 'Failed to publish post to Facebook.';
        setPostError(errorMessage);
        onPostError(errorMessage);
      }
    } catch (err: any) {
      console.error('Error posting to Facebook:', err);
      // Use the new helper function to parse the error
      const errorMessage = parseBackendError(err.response?.data);
      setPostError(errorMessage);
      onPostError(errorMessage);
    } finally {
      setIsPosting(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Review & Post to Facebook</CardTitle>
        <CardDescription>Review the AI-generated content before publishing.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {postError && <p className="text-red-500 mb-4">{postError}</p>}
        {postSuccess && <p className="text-green-500 mb-4">{postSuccess}</p>}

        <div>
          <Label htmlFor="post-caption">Post Caption</Label>
          <Textarea
            id="post-caption"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            rows={6}
            className="mt-1"
            disabled={isPosting}
          />
        </div>

        <div>
          <Label>Post Image</Label>
          {imagePath ? (
            <div className="w-full h-64 bg-gray-100 flex items-center justify-center overflow-hidden rounded-md mt-1">
              {/* Added a key to force re-render if imagePath changes, and a robust alt text */}
              <img key={imagePath} src={imagePath} alt={`Generated Post Visual for ${caption.substring(0, 20)}...`} className="object-contain max-h-full max-w-full" />
            </div>
          ) : (
            <p className="text-sm text-gray-500 mt-1">No image generated.</p>
          )}
          {/* In Phase 2, we will add an image upload input here */}
        </div>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline" onClick={onReset} disabled={isPosting}>
            Start Over
        </Button>
        <Button onClick={handlePostToFacebook} disabled={isPosting}>
          {isPosting ? 'Publishing...' : 'Publish to Facebook'}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default FacebookPostComposer;

