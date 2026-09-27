"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

import "katex/dist/katex.min.css";

const API_URL = "http://127.0.0.1:8000";

type Source = {
  source: string;
  page: number;
  similarity: number;
};

type Message = {
  id?: number;
  chat_id?: number;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  created_at?: string;
};

type Chat = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

type ChatDetail = Chat & {
  messages: Message[];
};

function AssistantMessage({
  message,
}: {
  message: Message;
}) {
  const [showSources, setShowSources] =
    useState(false);

  return (
    <div className="max-w-[85%] px-1 py-2">
      <div
        className="
          prose
          prose-invert
          max-w-none
          prose-p:my-3
          prose-p:leading-7
          prose-headings:mt-6
          prose-headings:mb-3
          prose-ul:my-3
          prose-ol:my-3
          prose-li:my-1
          prose-pre:border
          prose-pre:border-zinc-800
          prose-pre:bg-zinc-900
          prose-code:text-zinc-200
          prose-strong:text-zinc-100
        "
      >
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
                setShowSources(
                  (current) => !current
                )
              }
              className="text-xs text-zinc-500 transition hover:text-zinc-300"
            >
              {showSources
                ? "Ocultar fuentes"
                : `Mostrar fuentes (${message.sources.length})`}
            </button>

            {showSources && (
              <div className="mt-3 border-t border-zinc-800 pt-3">
                <div className="space-y-2">
                  {message.sources.map(
                    (
                      source,
                      sourceIndex
                    ) => (
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
  const [chats, setChats] =
    useState<Chat[]>([]);

  const [activeChatId, setActiveChatId] =
    useState<number | null>(null);

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [loadingChat, setLoadingChat] =
    useState(false);

  const [sidebarOpen, setSidebarOpen] =
    useState(true);

  const messagesEndRef =
    useRef<HTMLDivElement | null>(null);

  const textareaRef =
    useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const textarea = textareaRef.current;

    if (!textarea) return;

    textarea.style.height = "0px";

    const maxHeight = 180;

    const newHeight = Math.min(
      textarea.scrollHeight,
      maxHeight
    );

    textarea.style.height = `${newHeight}px`;

    textarea.style.overflowY =
      textarea.scrollHeight > maxHeight
        ? "auto"
        : "hidden";
  }, [input]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    async function initialize() {
      try {
        const loadedChats =
          await fetchChats();

        if (loadedChats.length > 0) {
          await openChat(
            loadedChats[0].id
          );
        }
      } catch (error) {
        console.error(
          "Error iniciando Jarvis:",
          error
        );
      }
    }

    void initialize();
  }, []);

  async function fetchChats(
    retries = 5
  ): Promise<Chat[]> {
    for (
      let attempt = 1;
      attempt <= retries;
      attempt++
    ) {
      try {
        const response = await fetch(
          `${API_URL}/chats`
        );

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}`
          );
        }

        const data: Chat[] =
          await response.json();

        setChats(data);

        return data;
      } catch (error) {
        if (attempt === retries) {
          throw error;
        }

        console.log(
          `Backend no disponible. Reintentando ${attempt}/${retries}...`
        );

        await new Promise(
          (resolve) =>
            setTimeout(
              resolve,
              1000
            )
        );
      }
    }

    return [];
  }

  async function createNewChat() {
    if (loading) return;

    try {
      const response = await fetch(
        `${API_URL}/chats`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            title: "Nuevo chat",
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const chat: Chat =
        await response.json();

      setChats((current) => [
        chat,
        ...current,
      ]);

      setActiveChatId(chat.id);
      setMessages([]);
      setInput("");

      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error(
        "Error creando chat:",
        error
      );
    }
  }

  async function openChat(
    chatId: number
  ) {
    if (loading) return;

    setLoadingChat(true);

    try {
      const response = await fetch(
        `${API_URL}/chats/${chatId}`
      );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const data: ChatDetail =
        await response.json();

      setActiveChatId(data.id);
      setMessages(
        data.messages ?? []
      );

      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error(
        "Error abriendo chat:",
        error
      );
    } finally {
      setLoadingChat(false);
    }
  }

  async function deleteChat(
    chatId: number
  ) {
    const confirmed = window.confirm(
      "¿Borrar esta conversación?"
    );

    if (!confirmed) return;

    try {
      const response = await fetch(
        `${API_URL}/chats/${chatId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      const remainingChats =
        chats.filter(
          (chat) =>
            chat.id !== chatId
        );

      setChats(remainingChats);

      if (
        activeChatId === chatId
      ) {
        if (
          remainingChats.length > 0
        ) {
          await openChat(
            remainingChats[0].id
          );
        } else {
          setActiveChatId(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error(
        "Error borrando chat:",
        error
      );
    }
  }

  async function ensureChat():
    Promise<number> {
    if (activeChatId !== null) {
      return activeChatId;
    }

    const response = await fetch(
      `${API_URL}/chats`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          title: "Nuevo chat",
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    const chat: Chat =
      await response.json();

    setActiveChatId(chat.id);

    setChats((current) => [
      chat,
      ...current,
    ]);

    return chat.id;
  }

  async function sendMessage() {
    const text = input.trim();

    if (!text || loading) {
      return;
    }

    setInput("");
    setLoading(true);

    try {
      const chatId =
        await ensureChat();

      const temporaryUserMessage:
        Message = {
          role: "user",
          content: text,
          sources: [],
        };

      setMessages((current) => [
        ...current,
        temporaryUserMessage,
      ]);

      const response = await fetch(
        `${API_URL}/chats/${chatId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            message: text,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }

      await response.json();

      const chatResponse =
        await fetch(
          `${API_URL}/chats/${chatId}`
        );

      if (!chatResponse.ok) {
        throw new Error(
          `HTTP ${chatResponse.status}`
        );
      }

      const chatData: ChatDetail =
        await chatResponse.json();

      setMessages(
        chatData.messages ?? []
      );

      await fetchChats();
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
    event:
      React.KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      void sendMessage();
    }
  }

  const activeChat =
    chats.find(
      (chat) =>
        chat.id === activeChatId
    );

  return (
    <main className="flex h-screen overflow-hidden bg-zinc-950 text-zinc-100">

      {sidebarOpen && (
        <aside
          className="
            flex
            w-72
            shrink-0
            flex-col
            border-r
            border-zinc-900
            bg-zinc-950
          "
        >
          <div className="p-3">
            <button
              onClick={createNewChat}
              className="
                w-full
                rounded-xl
                border
                border-zinc-800
                bg-zinc-900/60
                px-4
                py-3
                text-left
                text-sm
                transition
                hover:bg-zinc-900
              "
            >
              + Nuevo chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-2 pb-2">
            {chats.length === 0 && (
              <p className="px-3 py-4 text-sm text-zinc-600">
                Todavía no hay chats.
              </p>
            )}

            {chats.map((chat) => (
              <div
                key={chat.id}
                className="group relative"
              >
                <button
                  onClick={() =>
                    void openChat(
                      chat.id
                    )
                  }
                  className={
                    activeChatId ===
                    chat.id
                      ? `
                        mb-1
                        w-full
                        rounded-xl
                        bg-zinc-900
                        px-3
                        py-3
                        pr-10
                        text-left
                        text-sm
                        text-zinc-100
                      `
                      : `
                        mb-1
                        w-full
                        rounded-xl
                        px-3
                        py-3
                        pr-10
                        text-left
                        text-sm
                        text-zinc-500
                        transition
                        hover:bg-zinc-900/70
                        hover:text-zinc-200
                      `
                  }
                >
                  <span className="block truncate">
                    {chat.title}
                  </span>
                </button>

                <button
                  onClick={(event) => {
                    event.stopPropagation();

                    void deleteChat(
                      chat.id
                    );
                  }}
                  title="Borrar chat"
                  className="
                    absolute
                    right-2
                    top-2
                    hidden
                    h-8
                    w-8
                    items-center
                    justify-center
                    rounded-md
                    text-zinc-600
                    transition
                    hover:bg-zinc-800
                    hover:text-zinc-200
                    group-hover:flex
                  "
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="border-t border-zinc-900 p-4">
            <p className="text-sm font-medium text-zinc-300">
              Jarvis
            </p>

            <p className="mt-1 text-xs text-zinc-600">
              qwen3.5:9b + RAG local
            </p>
          </div>
        </aside>
      )}

      <div className="flex min-w-0 flex-1 flex-col">

        <header className="flex h-16 items-center gap-3 border-b border-zinc-900 px-4 md:px-6">
          <button
            onClick={() =>
              setSidebarOpen(
                (current) => !current
              )
            }
            className="flex h-9 w-9 items-center justify-center rounded-lg text-lg text-zinc-500 transition hover:bg-zinc-900 hover:text-zinc-100"
            title={
              sidebarOpen
                ? "Ocultar barra lateral"
                : "Mostrar barra lateral"
            }
          >
            ☰
          </button>

          <div className="min-w-0">
            <h1 className="truncate font-medium">
              {activeChat
                ? activeChat.title
                : "Jarvis"}
            </h1>

            <p className="text-xs text-zinc-600">
              qwen3.5:9b + RAG local
            </p>
          </div>
        </header>

        <section className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-4xl space-y-6 px-5 py-8 md:px-8">
            {loadingChat && (
              <div className="text-sm text-zinc-500">
                Cargando conversación...
              </div>
            )}

            {!loadingChat &&
              messages.length === 0 && (
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

            {messages.map(
              (
                message,
                index
              ) => (
                <div
                  key={
                    message.id ??
                    index
                  }
                  className={
                    message.role ===
                    "user"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }
                >
                  {message.role ===
                  "user" ? (
                    <div className="max-w-[80%] rounded-2xl bg-zinc-900 px-4 py-3">
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
              )
            )}

            {loading && (
              <div className="text-sm text-zinc-500">
                Jarvis está pensando...
              </div>
            )}

            <div
              ref={messagesEndRef}
            />
          </div>
        </section>

        <footer className="bg-zinc-950 px-4 pb-5 pt-3">
          <div className="mx-auto max-w-4xl">
            <div
              className="
                flex
                items-end
                gap-3
                rounded-2xl
                border
                border-zinc-800
                bg-zinc-900/70
                p-3
                shadow-sm
              "
            >
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(event) =>
                  setInput(
                    event.target.value
                  )
                }
                onKeyDown={
                  handleKeyDown
                }
                placeholder="Escribí un mensaje..."
                rows={1}
                disabled={loading}
                className="
                  min-h-[44px]
                  max-h-[180px]
                  flex-1
                  resize-none
                  overflow-y-hidden
                  bg-transparent
                  px-2
                  py-2
                  leading-6
                  outline-none
                  placeholder:text-zinc-600
                  disabled:opacity-50
                "
              />

              <button
                onClick={() =>
                  void sendMessage()
                }
                disabled={
                  loading ||
                  !input.trim()
                }
                className="
                  rounded-xl
                  bg-zinc-100
                  px-4
                  py-2
                  font-medium
                  text-zinc-950
                  transition
                  hover:bg-white
                  disabled:cursor-not-allowed
                  disabled:opacity-30
                "
              >
                Enviar
              </button>
            </div>

            <p className="mt-2 text-center text-xs text-zinc-700">
              Shift + Enter para salto de línea
            </p>
          </div>
        </footer>
      </div>
    </main>
  );
}
