// src/frontend/src/app/history/page.tsx
"use client";

import { ErrorMessage } from "@/components/assistant-message";
import RecentChat from "@/components/recent-chat";
import { Separator } from "@/components/ui/separator";
import { useChatHistory } from "@/hooks/history";
import { HistoryIcon } from "lucide-react";
import React, { useState } from "react";
import { Toast, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport } from "@/components/ui/toast"; // Import toast components
import { Button } from "@/components/ui/button";

export default function RecentsPage() {
  const { data: chats, isLoading, error } = useChatHistory();
  const [showToast, setShowToast] = useState(false); // State for toast visibility

  if (!error && !chats) return <div>Loading...</div>;

  return (
    <div className="h-screen ">
      <div className="mx-auto max-w-3xl pt-16 px-4 pb-16">
        <div className="flex items-center space-x-2 mb-3">
          <HistoryIcon className="w-5 h-5" />
          <h1 className="text-xl font-semibold">Chat History</h1>
        </div>
        <Separator className="mb-4" />

        {/* Button to trigger the toast */}
        <Button onClick={() => setShowToast(true)}>Show Toast</Button>

        {/* Toast Modal */}
        <ToastProvider>
          {showToast && (
            <Toast open={showToast} onOpenChange={setShowToast}>
              {" "}
              {/* Control visibility with state */}
              <ToastTitle>Toast Title</ToastTitle>
              <ToastDescription>This is a toast message.</ToastDescription>
              <Button variant="destructive" size="sm" onClick={() => setShowToast(false)}>
                {" "}
                {/* Close button for toast*/}
                Cancel
              </Button>
            </Toast>
          )}
          <ToastViewport />
        </ToastProvider>

        {error && <ErrorMessage content={error.message} />}
        {chats && (
          <ul className="flex flex-col gap-4">
            {chats.map((chat, index) => (
              <React.Fragment key={chat.id}>
                <RecentChat {...chat} />
                {index < chats.length - 1 && <Separator className="" />}
              </React.Fragment>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
