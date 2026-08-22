"use client";

import { useState } from "react";

import ChatInput from "@/components/chat/ChatInput";
import ChatMessage, { Message } from "@/components/chat/ChatMessage";
import QuickActions from "@/components/chat/QuickActions";

const WELCOME: Message = {
  role: "assistant",
  content:
    "Hi! Tell me what's going on and I'll help you find the right doctor, check symptoms, find a pharmacy, or book an appointment.",
};

function newThreadId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return Math.random().toString(36).slice(2);
}

export default function ChatWindow() {
  const [threadId] = useState(newThreadId);
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [sending, setSending] = useState(false);

  async function send(text: string) {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, thread_id: threadId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.error ?? "Something went wrong." }]);
        return;
      }
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply, doctorRecommendations: data.doctor_recommendations ?? undefined },
      ]);
    } finally {
      setSending(false);
    }
  }

  const isFresh = messages.length === 1;

  return (
    <div className="flex flex-1 flex-col">
      <div className="mb-4">
        <h1 className="text-xl font-semibold text-slate-900">How can we help today?</h1>
        <p className="mt-1 text-sm text-slate-500">
          Describe what&apos;s going on in your own words, or pick a quick option below.
        </p>
      </div>

      {isFresh && (
        <div className="mb-4">
          <QuickActions onPick={send} />
        </div>
      )}

      <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-50 shadow-sm">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((m, i) => (
            <ChatMessage key={i} message={m} />
          ))}
          {sending && (
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-600 text-xs font-semibold text-white">
                H
              </div>
              <div className="rounded-2xl rounded-tl-sm bg-white px-3.5 py-2.5 text-sm text-slate-400 shadow-sm ring-1 ring-slate-200">
                Thinking…
              </div>
            </div>
          )}
        </div>
        <div className="border-t border-slate-200 bg-white p-3">
          <ChatInput onSend={send} disabled={sending} />
        </div>
      </div>
    </div>
  );
}
