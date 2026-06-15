import { useCallback, useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import { ChatPage } from "./pages/ChatPage";
import { MemoryPage } from "./pages/MemoryPage";
import { PatternPage } from "./pages/PatternPage";
import { TaskPage } from "./pages/TaskPage";
import type { ChatMessage } from "./pages/ChatPage";
import type { ChatResponse } from "./services/chatService";

const CHAT_STORAGE_KEY = "growth-agent-chat-state-v1";

type StoredChatState = {
  userId: string;
  conversationId?: string;
  messages: ChatMessage[];
  lastResponse: ChatResponse | null;
};

const EMPTY_STATE: StoredChatState = {
  userId: "demo-user",
  conversationId: undefined,
  messages: [],
  lastResponse: null
};

function loadStoredState(): StoredChatState {
  if (typeof window === "undefined") return EMPTY_STATE;
  try {
    const raw = window.localStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return EMPTY_STATE;
    const parsed = JSON.parse(raw) as Partial<StoredChatState>;
    return {
      userId: typeof parsed.userId === "string" ? parsed.userId : EMPTY_STATE.userId,
      conversationId:
        typeof parsed.conversationId === "string" ? parsed.conversationId : undefined,
      messages: Array.isArray(parsed.messages) ? (parsed.messages as ChatMessage[]) : [],
      lastResponse: (parsed.lastResponse as ChatResponse | null) ?? null
    };
  } catch {
    return EMPTY_STATE;
  }
}

const navItems = [
  { to: "/chat", label: "对话" },
  { to: "/memories", label: "记忆" },
  { to: "/patterns", label: "模式" },
  { to: "/tasks", label: "任务" }
];

export default function App() {
  const [chatState, setChatState] = useState<StoredChatState>(() => loadStoredState());

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(chatState));
    } catch {
      // ignore quota / private-mode failures
    }
  }, [chatState]);

  const updateChat = useCallback((patch: Partial<StoredChatState>) => {
    setChatState((current) => ({ ...current, ...patch }));
  }, []);

  const appendMessage = useCallback((message: ChatMessage) => {
    setChatState((current) => ({ ...current, messages: [...current.messages, message] }));
  }, []);

  const replaceLastResponse = useCallback((response: ChatResponse) => {
    setChatState((current) => ({
      ...current,
      conversationId: response.conversation_id,
      lastResponse: response
    }));
  }, []);

  const resetChat = useCallback(() => {
    setChatState((current) => ({
      ...current,
      conversationId: undefined,
      messages: [],
      lastResponse: null
    }));
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">成</span>
          <div>
            <h1>成长智能体</h1>
            <p>记忆驱动成长工作台</p>
          </div>
        </div>
        <nav className="nav-list" aria-label="Primary navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="workspace">
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route
            path="/chat"
            element={
              <ChatPage
                userId={chatState.userId}
                conversationId={chatState.conversationId}
                messages={chatState.messages}
                lastResponse={chatState.lastResponse}
                onChangeUserId={(userId) => updateChat({ userId })}
                onAppendMessage={appendMessage}
                onReplaceLastResponse={replaceLastResponse}
                onResetChat={resetChat}
              />
            }
          />
          <Route path="/memories" element={<MemoryPage userId={chatState.userId} />} />
          <Route path="/patterns" element={<PatternPage userId={chatState.userId} />} />
          <Route path="/tasks" element={<TaskPage userId={chatState.userId} />} />
        </Routes>
      </main>
    </div>
  );
}
