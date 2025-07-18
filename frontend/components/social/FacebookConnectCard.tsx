// components/social/FacebookConnectCard.tsx
"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Facebook, Link, Unlink } from "lucide-react";

interface FacebookStatus {
  access_token_status: 'valid' | 'missing';
  permissions_ok: boolean;
}

interface FacebookConnectCardProps {
  agentId: string;
  status: FacebookStatus | null;
  onConnectionChange: (newStatus: FacebookStatus) => void;
}

export default function FacebookConnectCard({ agentId, status, onConnectionChange }: FacebookConnectCardProps) {

  const handleConnect = () => {
    // Redirect to the backend OAuth login URL
    window.location.href = `/api/facebook/auth/login?agent_id=${agentId}`;
  };

  const isConnected = status?.access_token_status === 'valid' && status?.permissions_ok;

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-md">
       <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
        Social Connections
      </h3>
      <div className={cn(
          "flex items-center justify-between p-4 rounded-lg",
          isConnected ? "bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800" : "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
      )}>
        <div className="flex items-center gap-3">
            <Facebook className={cn("h-6 w-6", isConnected ? "text-green-600" : "text-blue-600")} />
            <div>
                <p className="font-semibold text-gray-800 dark:text-gray-200">Facebook Page</p>
                <p className={cn("text-sm", isConnected ? "text-green-700 dark:text-green-400" : "text-blue-700 dark:text-blue-400")}>
                    {isConnected ? "Connected & Ready" : "Not Connected"}
                </p>
            </div>
        </div>
        <Button 
          size="sm" 
          variant={isConnected ? "destructive" : "default"}
          onClick={handleConnect} // For now, both connect and disconnect point to the same flow
        >
          {isConnected ? <Unlink className="mr-2 h-4 w-4" /> : <Link className="mr-2 h-4 w-4" />}
          {isConnected ? "Reconnect" : "Connect"}
        </Button>
      </div>
       <p className="text-xs text-gray-500 mt-3">
        Connect your Facebook page to automatically publish posts generated by the AI.
      </p>
    </div>
  );
}

