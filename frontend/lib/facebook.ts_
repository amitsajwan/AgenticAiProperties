// lib/facebook.ts
import axios from "axios";

const facebookApi = axios.create({
  baseURL: "/api/facebook",
  headers: { "Content-Type": "application/json" },
});

export const facebook = {
  // Start the OAuth login flow
  connect: (agentId: string) =>
    facebookApi.get("/auth/login", { params: { agent_id: agentId } }),

  // Create a new post via your multipart endpoint
  post: (data: FormData) => facebookApi.post("/posts", data),

  // Fetch existing posts for listing
  getPosts: (agentId: string) =>
    facebookApi.get(`/posts?agent_id=${agentId}`),
};

