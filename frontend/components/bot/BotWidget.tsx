"use client";

import { useEffect, useRef, useState } from "react";
import { Send, AlertCircle } from "lucide-react";
import { useChatScroll } from "@/lib/hooks/use-chat-scroll";
import { cn } from "@/lib/utils";
import { MessageSquare as BotMessageSquare, UserCircle2 } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

// [MODIFIED] - Helper function to construct WebSocket URL dynamically
const getWebSocketURL = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    // Assumes backend runs on port 8000. For production, use a reverse proxy or environment variables.
    const port = '8000';
    // The path needs to match the backend router configuration.
    const path = '/api/bot/chat?client_id=user123'; // Added client_id as per backend expectation
    return `${protocol}//${host}:${port}${path}`;
};


export default function BotWidget() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useChatScroll(messages);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connectWebSocket = () => {
    try {
      // [MODIFIED] - Use the dynamic URL
      ws.current = new WebSocket(getWebSocketURL());

      ws.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log("WebSocket connected");
      };

      ws.current.onmessage = (event) => {
        try {
          // The backend sends a simple text response now, not JSON
          const messageContent = event.data;
          setMessages((prev) => [...prev, {
            role: "assistant",
            content: messageContent,
            timestamp: new Date()
          }]);
          setIsLoading(false);
        } catch (err) {
          console.error("Error processing message:", err);
          setError("Error processing server response");
          setIsLoading(false);
        }
      };

      ws.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setError("Connection error. Is the backend server running on port 8000?");
        setIsConnected(false);
        setIsLoading(false);
      };

      ws.current.onclose = (event) => {
        setIsConnected(false);
        setIsLoading(false);
        console.log("WebSocket disconnected:", event.code, event.reason);
        if (event.code !== 1000) { // Not a normal closure
          if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log("Attempting to reconnect...");
            connectWebSocket();
          }, 3000);
        }
      };
    } catch (err) {
      console.error("Error creating WebSocket:", err);
      setError("Failed to connect to chat service");
      setIsConnected(false);
    }
  };

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close(1000, "Component unmounting");
      }
    };
  }, []);

  const sendMessage = () => {
    if (!input.trim() || !isConnected || isLoading) return;

    const message: Message = { 
      role: "user", 
      content: input,
      timestamp: new Date()
    };
    setMessages((prev) => [...prev, message]);
    setIsLoading(true);
    setError(null);
    
    try {
      // The backend expects a simple text message
      ws.current?.send(input);
      setInput("");
    } catch (err) {
      console.error("Error sending message:", err);
      setError("Failed to send message");
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full p-4 bg-white dark:bg-gray-900 rounded-2xl shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
          Chat Assistant
        </h3>
        <div className="flex items-center space-x-2">
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500" : "bg-red-500"
          )} />
          <span className="text-xs text-gray-500">
            {isConnected ? "Online" : "Offline"}
          </span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
           <p>Start a conversation!</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={cn("flex gap-2 items-end", msg.role === "user" ? "justify-end" : "justify-start")}
          >
            {msg.role === "assistant" && (
              <Avatar className="h-6 w-6 flex-shrink-0">
                <AvatarFallback>
                  <BotMessageSquare className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
            <div
              className={cn(
                "px-3 py-2 rounded-xl max-w-xs whitespace-pre-wrap text-sm",
                msg.role === "user"
                   ? "bg-blue-500 text-white user-message"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white bot-message"
              )}
            >
              {msg.content}
            </div>
            {msg.role === "user" && (
              <Avatar className="h-6 w-6 flex-shrink-0">
                <AvatarFallback>
                  <UserCircle2 className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start items-end gap-2">
             <Avatar className="h-6 w-6 flex-shrink-0">
                <AvatarFallback>
                  <BotMessageSquare className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            <div className="bg-gray-100 dark:bg-gray-800 px-3 py-2 rounded-xl">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
         
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex">
        <input
          className="flex-1 border border-gray-300 dark:border-gray-600 rounded-l-xl px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 text-black dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          onKeyDown={handleKeyPress}
          disabled={!isConnected || isLoading}
        />
        <button
          className={cn(
            "px-4 py-2 rounded-r-xl text-white transition-colors flex items-center justify-center",
            isConnected && !isLoading && input.trim()
              ? "bg-blue-500 hover:bg-blue-600"
              : "bg-gray-400 cursor-not-allowed"
          )}
          onClick={sendMessage}
          disabled={!isConnected || isLoading || !input.trim()}
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

