"use client";

import { useState } from "react";
import { sendMessage } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [cvFile, setCvFile] = useState<File | null>(null);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const messageText = input;

    const userMessage: Message = {
      role: "user",
      content: messageText,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendMessage(messageText, cvFile ?? undefined);

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Clear CV only AFTER successful sending
      setCvFile(null);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setLoading(false);
    }
  };
  return (
    <main className="flex min-h-screen flex-col bg-gray-100">
      <header className="border-b bg-white p-4">
        <h1 className="text-xl font-bold">AI Job Agent</h1>
      </header>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3x1 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`rounded-lg p-4 ${message.role === "user" ? "ml-auto bg-blue-500 text-white" : "mr-auto bg-white"}`}
            >
              {message.content}
            </div>
          ))}

          {loading && (
            <div className="rounded-lg bg-white p-4">Searching for Jobs...</div>
          )}
        </div>
      </div>
      <div className="border-t bg-white p-4">
        <div className="mx-auto flex max-w-3xl gap-2">
          <input
            className="flex-1 rounded-lg border p-3"
            placeholder="What job are you looking for?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSend();
              }
            }}
          />

          <button
            onClick={handleSend}
            className="rounded-lg bg-blue-600 px-6 py-3 text-white"
          >
            Send
          </button>
          <button
            onClick={() => {
              const fileInput = document.getElementById(
                "cvFileInput",
              ) as HTMLInputElement;
              if (fileInput) {
                fileInput.click();
              }
            }}
            className="rounded-lg bg-gray-300 px-6 py-3 text-gray-700"
          >
            Upload CV
          </button>
          <input
            type="file"
            id="cvFileInput"
            accept=".pdf,.doc,.docx"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0] ?? null;
              setCvFile(file);
            }}
          />
        </div>
      </div>
    </main>
  );
}
