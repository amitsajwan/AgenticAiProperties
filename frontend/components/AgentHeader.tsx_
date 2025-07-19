"use client";

import React from "react";

interface AgentHeaderProps {
  name: string;
  profileImageUrl?: string;
  businessName?: string;
}

export default function AgentHeader({
  name,
  profileImageUrl,
  businessName,
}: AgentHeaderProps) {
  return (
    <div className="flex items-center justify-between bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-md">
      <div className="flex items-center space-x-4">
        {profileImageUrl ? (
          <img
            src={profileImageUrl}
            alt={name}
            className="h-12 w-12 rounded-full object-cover"
          />
        ) : (
          <div className="h-12 w-12 rounded-full bg-gray-200 dark:bg-gray-700" />
        )}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {businessName || name}
          </h1>
          {name && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{name}</p>
          )}
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <span className="inline-block w-3 h-3 rounded-full bg-green-500" />
        <p className="text-sm text-gray-500 dark:text-gray-300">Online</p>
      </div>
    </div>
  );
}


