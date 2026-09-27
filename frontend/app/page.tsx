"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

import "katex/dist/katex.min.css";

type Source = {
  source: string;
  page: number;
  similarity: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

function AssistantMessage({
  message,
}: {
  message: Message;
}) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className="max-w-[85%] px-1 py-2">
      <div className="prose prose-invert max-w-none prose-p:leading-7 prose-pre:bg-zinc-900">
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
        >
          {message.content}
        </ReactMarkdown>
      </div>

      {message.sources &&
        message.sources.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() =>
                setShowSources((current) => !current)
              }
              className="text-xs text-zinc-500 hover:text-zinc-300"
            >
              {showSources
                ? "Ocultar fuentes"
                : `Mostrar fuentes (${message.sources.length})`}
            </button>

            {showSources && (
              <div className="mt-3 border-t border-zinc-800 pt-3">
                <div className="space-y-2">
                  {message.sources.map(
                    (source, sourceIndex) => (
                      <div
                        key={sourceIndex}
                        className="text-sm text-zinc-400"
                      >
                        <span>
                          {source.source}
                        </span>

                        <span className="text-zinc-600">
                          {" "}
                          — pág. {source.page}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        )}
    </div>
  );
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    const text = input.trim();

    if (!text || loading) return;

    const newUserMessage: Message = {
      role: "user",
      content: text,
    };

    setMessages((current) => [
      ...current,
      newUserMessage,
    ]);

    setInput("");
    setLoading(true);

    try {
      const history = messages.map((message) => ({
        role: message.role,
        content: message.content,
      }));

      const response = await fetch(
        "http://127.0.0.1:8000/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: text,
            history,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer,
        sources: data.sources ?? [],
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
    } catch (error) {
      console.error(error);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "Hubo un error conectando con Jarvis.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-4xl flex-col">
        <header className="border-b border-zinc-800 px-6 py-4">
          <h1 className="text-xl font-semibold">
            Jarvis
          </h1>

          <p className="text-sm text-zinc-500">
            qwen3.5:9b + RAG local
          </p>
        </header>

        <section className="flex-1 space-y-6 overflow-y-auto px-6 py-8">
          {messages.length === 0 && (
            <div className="mt-24 text-center">
              <h2 className="text-2xl font-semibold">
                ¿Qué ocupás?
              </h2>

              <p className="mt-2 text-zinc-500">
                Preguntame sobre tus libros,
                física, matemática o lo que sea.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={
                message.role === "user"
                  ? "flex justify-end"
                  : "flex justify-start"
              }
            >
              {message.role === "user" ? (
                <div className="max-w-[80%] rounded-2xl bg-zinc-800 px-4 py-3">
                  <p className="whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
              ) : (
                <AssistantMessage
                  message={message}
                />
              )}
            </div>
          ))}

          {loading && (
            <div className="text-sm text-zinc-500">
              Jarvis está pensando...
            </div>
          )}
        </section>

        <footer className="border-t border-zinc-800 bg-zinc-950 p-4">
          <div className="flex items-end gap-3 rounded-2xl border border-zinc-700 bg-zinc-900 p-3">
            <textarea
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Escribí un mensaje..."
              rows={1}
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 outline-none placeholder:text-zinc-600"
            />

            <button
              onClick={sendMessage}
              disabled={
                loading ||
                !input.trim()
              }
              className="rounded-xl bg-white px-4 py-2 font-medium text-black disabled:cursor-not-allowed disabled:opacity-30"
            >
              Enviar
            </button>
          </div>

          <p className="mt-2 text-center text-xs text-zinc-600">
            Shift + Enter para salto de línea
          </p>
        </footer>
      </div>
    </main>
  );
}