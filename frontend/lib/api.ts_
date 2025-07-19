import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" }
});



export async function generateAndPublish(
  agentId: string,
  prompt: string
) {
  const resp = await api.post("/bot/generate-content", {
    agent_id: agentId,
    prompt,
  });
  return resp.data;  // { message, url, images[], scheduled, ... }
}

export default api;


