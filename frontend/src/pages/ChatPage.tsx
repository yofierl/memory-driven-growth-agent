import { FormEvent, useState } from "react";

import { ChatResponse, postChat } from "../services/chatService";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export function ChatPage() {
  const [userId, setUserId] = useState("demo-user");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = input.trim();
    if (!message || isSending) {
      return;
    }
    setInput("");
    setError(null);
    setIsSending(true);
    setMessages((current) => [...current, { role: "user", content: message }]);
    try {
      const response = await postChat({
        user_id: userId.trim() || "demo-user",
        conversation_id: conversationId,
        message
      });
      setConversationId(response.conversation_id);
      setLastResponse(response);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: response.assistant_response }
      ]);
    } catch {
      setError("Request failed. Check that the backend is running on VITE_API_BASE_URL.");
    } finally {
      setIsSending(false);
    }
  }

  const riskLevel = lastResponse?.risk_level ?? "none";
  const riskClass = riskLevel === "high" || riskLevel === "medium" ? "is-alert" : "";

  return (
    <section className="page">
      <header className="page-header">
        <p className="eyebrow">Conversation</p>
        <h2>Chat</h2>
      </header>
      <div className="disclaimer-panel">
        <p>
          This product supports self-growth reflection and daily planning. It is
          not medical diagnosis, psychotherapy, crisis intervention, or emergency
          support. If you are in immediate danger, contact local emergency
          services or a trusted nearby person now.
        </p>
      </div>

      <div className="chat-layout">
        <div className="chat-main">
          <div className="chat-thread" aria-live="polite">
            {messages.length === 0 ? (
              <p className="chat-placeholder">
                Send a demo message to run the full LangGraph workflow.
              </p>
            ) : (
              messages.map((message, index) => (
                <article key={`${message.role}-${index}`} className={`chat-message ${message.role}`}>
                  <p>{message.content}</p>
                </article>
              ))
            )}
          </div>

          <form className="chat-form" onSubmit={handleSubmit}>
            <label>
              User
              <input value={userId} onChange={(event) => setUserId(event.target.value)} />
            </label>
            <label className="chat-input">
              Message
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                rows={4}
              />
            </label>
            <button className="primary-button" type="submit" disabled={isSending || !input.trim()}>
              {isSending ? "Sending" : "Send"}
            </button>
          </form>
          {error ? <p className="chat-error">{error}</p> : null}
        </div>

        <aside className="chat-side-panel">
          <div>
            <p className="panel-label">Strategy</p>
            <strong>{lastResponse?.strategy ?? "not started"}</strong>
          </div>
          <div>
            <p className="panel-label">Risk</p>
            <span className={`risk-badge ${riskClass}`}>{riskLevel}</span>
            {lastResponse?.risk_reason ? <p className="risk-reason">{lastResponse.risk_reason}</p> : null}
          </div>
          <div>
            <p className="panel-label">Retrieved Memories</p>
            <strong>{lastResponse?.retrieved_memories.length ?? 0}</strong>
          </div>
          {lastResponse?.generated_task ? (
            <div className="generated-task">
              <p className="panel-label">Generated Task</p>
              <strong>{lastResponse.generated_task.task_content}</strong>
              <span>
                {lastResponse.generated_task.difficulty ?? "low"} ·{" "}
                {lastResponse.generated_task.duration_minutes ?? 15} min
              </span>
            </div>
          ) : null}
        </aside>
      </div>
    </section>
  );
}
