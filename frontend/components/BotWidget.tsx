"use client";

import { useEffect, useRef, useState } from "react";
import { Send, AlertCircle, MessageSquare, UserCircle2 } from "lucide-react";
import { useChatScroll } from "@/lib/hooks/use-chat-scroll";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "./ui/avatar";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface BotWidgetProps {
  agentId?: string;
}

export default function BotWidget({ agentId }: BotWidgetProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useChatScroll(messages);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const clientId = agentId || "anonymous_user";
    ws.current = new WebSocket(`ws://localhost:8000/api/bot/chat?client_id=${clientId}`);

    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => {
      setConnected(false);
      console.warn("WebSocket closed");
    };

    ws.current.onmessage = (e) => {
      try {
        const isJson = e.data.startsWith("{");
        const data = isJson ? JSON.parse(e.data) : { message: e.data };
        setMessages((m) => [...m, { role: "assistant", content: data.message }]);
      } catch (err) {
        console.error("Invalid WebSocket message:", e.data);
      }
      setLoading(false);
    };

    ws.current.onerror = () => {
      setError("WebSocket connection failed");
      setConnected(false);
    };

    return () => ws.current?.close();
  }, [agentId]);

  const send = () => {
    if (!input.trim() || !connected) return;
    setMessages((m) => [...m, { role: "user", content: input }]);
    setLoading(true);
    ws.current?.send(input); // Send plain text
    setInput("");
  };

  return (
    <div className="flex flex-col h-full p-4 bg-white dark:bg-gray-900 rounded-xl shadow">
      <div className="flex-1 overflow-y-auto space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            {m.role === "assistant" && (
              <Avatar className="h-6 w-6 mr-2">
                <AvatarFallback>
                  <MessageSquare />
                </AvatarFallback>
              </Avatar>
            )}
            <div
              className={cn(
                "px-3 py-2 rounded-xl max-w-xs break-words",
                m.role === "user" ? "bg-blue-500 text-white" : "bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-white"
              )}
            >
              {m.content}
            </div>
            {m.role === "user" && (
              <Avatar className="h-6 w-6 ml-2">
                <AvatarFallback>
                  <UserCircle2 />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="mt-4 flex">
        <input
          className="flex-1 border rounded-l px-3"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
        />
        <button onClick={send} className="px-4 bg-blue-500 rounded-r text-white disabled:opacity-60" disabled={!connected}>
          <Send />
        </button>
      </div>
      {error && (
        <div className="mt-2 text-red-600 flex items-center">
          <AlertCircle className="mr-1" /> {error}
        </div>
      )}
    </div>
  );
}

