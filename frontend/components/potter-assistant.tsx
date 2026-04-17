"use client";

import { useState } from "react";

import { PotterChatResponse } from "@/lib/types";

interface ChatEntry {
  role: "assistant" | "user";
  text: string;
}

const DEFAULT_PROMPTS = [
  "How does your process work?",
  "What is my paper portfolio doing right now?",
  "What market has the strongest edge right now?",
];

export function PotterAssistant() {
  const [messages, setMessages] = useState<ChatEntry[]>([
    {
      role: "assistant",
      text: "I’m Potter. Ask me how I work, what my portfolio is doing, or what I think about a specific market.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [prompts, setPrompts] = useState<string[]>(DEFAULT_PROMPTS);

  async function sendMessage(rawMessage: string) {
    const message = rawMessage.trim();
    if (!message || loading) {
      return;
    }

    setLoading(true);
    setInput("");
    setMessages((current) => [...current, { role: "user", text: message }]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      const data = (await response.json()) as PotterChatResponse;
      setMessages((current) => [...current, { role: "assistant", text: data.answer }]);
      setPrompts(data.suggested_prompts.length > 0 ? data.suggested_prompts : DEFAULT_PROMPTS);
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: "I hit a connection problem talking to the live backend. Try again in a moment.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel assistant-panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Potter Assistant</span>
          <h2>Ask Potter</h2>
        </div>
        <div className="assistant-status">
          <div className={`potter-avatar ${loading ? "thinking" : ""}`} aria-hidden="true">
            <span className="potter-head-shape" />
            <span className="potter-eye left" />
            <span className="potter-eye right" />
            <span className="potter-mouth" />
          </div>
        </div>
      </div>

      <p className="assistant-copy">
        Potter answers from the live portfolio, trade log, current market board, and ingestion state.
      </p>

      <div className="assistant-prompts">
        {prompts.map((prompt) => (
          <button key={prompt} type="button" className="mini-pill button-pill" onClick={() => sendMessage(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <div className="assistant-thread">
        {messages.map((message, index) => (
          <article key={`${message.role}-${index}`} className={`assistant-message ${message.role}`}>
            <strong>{message.role === "assistant" ? "Potter" : "You"}</strong>
            <p>{message.text}</p>
          </article>
        ))}
      </div>

      <form
        className="assistant-form"
        onSubmit={(event) => {
          event.preventDefault();
          void sendMessage(input);
        }}
      >
        <input
          className="assistant-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask Potter about a market, the process, or your portfolio..."
        />
        <button type="submit" className="assistant-send" disabled={loading}>
          {loading ? "Thinking..." : "Send"}
        </button>
      </form>
    </section>
  );
}
