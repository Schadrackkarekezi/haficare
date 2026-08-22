"use client";

import { useState } from "react";

export default function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled?: boolean }) {
  const [value, setValue] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  }

  return (
    <form onSubmit={submit} className="flex gap-2">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder="Describe your symptoms, or ask for a doctor, pharmacy, or appointment…"
        className="flex-1 rounded-full border border-slate-300 px-4 py-2 text-sm focus:border-teal-500 focus:outline-none disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled}
        className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
      >
        Send
      </button>
    </form>
  );
}
