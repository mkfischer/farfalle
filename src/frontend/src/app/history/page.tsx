"use client";
import { ErrorMessage } from "@/components/assistant-message";
import RecentChat from "@/components/recent-chat";
import { Separator } from "@/components/ui/separator";
import { useChatHistory } from "@/hooks/history";
import { HistoryIcon } from "lucide-react";
import React, { useState, useEffect } from "react";
import { Toast, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";

export default function RecentsPage() {
  const { data: chats, isLoading, error, refetch } = useChatHistory();
  const [showToast, setShowToast] = useState(false);

  const handleClearHistory = async () => {
    console.log("Clearing chat history...");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      console.log("API URL:", apiUrl);
      const response = await fetch(`${apiUrl}/history`, { method: "DELETE" });
      console.log("Response:", response);
      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail || "Failed to clear history";
        console.error("Error clearing history:", errorMessage);
        throw new Error(errorMessage);
      }
      console.log("Chat history cleared successfully.");
      refetch();
      setShowToast(false);
    } catch (error) {
      console.error("Error clearing history:", error);
      setShowToast(false);
    }
  };

  useEffect(() => {
    console.log("Chats data:", chats);
  }, [chats]);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <ErrorMessage content={error.message} />;
  if (!chats) return <div>No chats found.</div>;

  return (
    <div className="h-screen">
      <div className="mx-auto max-w-3xl pt-16 px-4 pb-16">
        <div className="flex items-center space-x-2 mb-3">
          <HistoryIcon className="w-5 h-5" />
          <h1 className="text-xl font-semibold">Chat History</h1>
        </div>
        <Separator className="mb-4" />
        <Button onClick={() => setShowToast(true)}>Clear History</Button>
        <ToastProvider>
          {showToast && (
            <Toast open={showToast} onOpenChange={(open) => setShowToast(open)}>
              <div className="flex space-x-2">
                <div className="grid gap-1">
                  <ToastTitle>Are you sure?</ToastTitle>
                  <ToastDescription>This will clear the history.</ToastDescription>
                </div>
                <ToastClose />
              </div>
              <div className="grid grid-flow-col gap-2">
                <Button variant="destructive" size="sm" onClick={handleClearHistory}>
                  Continue
                </Button>
                <Button variant="destructive" size="sm" onClick={() => setShowToast(false)}>
                  Cancel
                </Button>
              </div>
            </Toast>
          )}
          <ToastViewport />
        </ToastProvider>
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
