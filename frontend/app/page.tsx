"use client";

import { useState } from "react";
import { sendMessage } from "@/lib/api";
import ChatMessage from "@/components/ChatMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    setError(null);

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
      setError("We couldn’t complete the search. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  return (
    <main className="flex min-h-screen flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-5">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600">
              Career search
            </p>
            <h1 className="mt-1 text-xl font-bold text-slate-900">
              AI Job Agent
            </h1>
          </div>
          <span className="hidden rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 sm:block">
            Ready to search
          </span>
        </div>
      </header>
      <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-4xl space-y-4">
          {messages.length === 0 && (
            <section className="mx-auto max-w-2xl rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-12">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-2xl">
                ✦
              </div>
              <h2 className="mt-5 text-2xl font-bold text-slate-900">
                Your Job Search
              </h2>
              <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-600">
                Tell me what kind of role you’re looking for, or upload your CV
                and I’ll find relevant jobs in the German market.
              </p>
            </section>
          )}
          {messages.map((message, index) => (
            <ChatMessage key={`${message.role}-${index}`} {...message} />
          ))}

          {loading && (
            <div className="flex items-center gap-3 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-5 py-4 text-sm text-slate-600 shadow-sm">
              <span className="flex gap-1" aria-hidden="true">
                <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.2s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.1s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500" />
              </span>
              Searching for matching jobs…
            </div>
          )}
          {error && (
            <p
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </p>
          )}
        </div>
      </div>
      <div className="border-t border-slate-200 bg-white p-4">
        <div className="mx-auto max-w-4xl">
          {cvFile && (
            <div className="mb-3 flex items-center justify-between rounded-xl bg-blue-50 px-3 py-2 text-sm text-blue-800">
              <span className="truncate">CV attached: {cvFile.name}</span>
              <button
                type="button"
                onClick={() => setCvFile(null)}
                className="ml-3 font-medium hover:text-blue-950"
                aria-label="Remove attached CV"
              >
                Remove
              </button>
            </div>
          )}
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              className="min-w-0 flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
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
              type="button"
              onClick={() => {
                const fileInput = document.getElementById(
                  "cvFileInput",
                ) as HTMLInputElement;
                if (fileInput) {
                  fileInput.click();
                }
              }}
              className="rounded-xl border border-slate-300 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              {cvFile ? "Change CV" : "Upload CV"}
            </button>
            <button
              type="button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Search jobs
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
      </div>
    </main>
  );
}
