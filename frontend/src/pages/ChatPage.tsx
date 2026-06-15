import { FormEvent, useCallback, useState } from "react";

import { apiClient } from "../api/client";
import { ChatResponse, postChat } from "../services/chatService";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ChatPageProps = {
  userId: string;
  conversationId?: string;
  messages: ChatMessage[];
  lastResponse: ChatResponse | null;
  onChangeUserId: (userId: string) => void;
  onAppendMessage: (message: ChatMessage) => void;
  onReplaceLastResponse: (response: ChatResponse) => void;
};

const STRATEGY_LABELS: Record<string, string> = {
  emotional_support: "情绪支持",
  information_follow_up: "信息追问",
  task_review: "任务复盘",
  safety_response: "安全回应",
  safety_handled: "安全处理",
  not_started: "尚未开始"
};

const RISK_LABELS: Record<string, string> = {
  none: "无风险",
  low: "低风险",
  medium: "中风险",
  high: "高风险"
};

const DIFFICULTY_LABELS: Record<string, string> = {
  low: "低",
  adjusted: "已调整"
};

function labelFromMap(map: Record<string, string>, value: string | undefined, fallback: string) {
  if (!value) return fallback;
  return map[value] ?? value;
}

function displayRiskReason(reason: string | null | undefined) {
  if (!reason) return null;
  return /[\u4e00-\u9fff]/.test(reason) ? reason : "系统已完成风险检查。";
}

export function ChatPage(props: ChatPageProps) {
  const {
    userId,
    conversationId,
    messages,
    lastResponse,
    onChangeUserId,
    onAppendMessage,
    onReplaceLastResponse
  } = props;
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingPatternId, setPendingPatternId] = useState<string | null>(null);
  const [resolvedPatternIds, setResolvedPatternIds] = useState<Record<string, "confirmed" | "rejected">>({});

  const submitPatternFeedback = useCallback(
    async (patternId: string, status: "confirmed" | "rejected") => {
      setPendingPatternId(patternId);
      setError(null);
      try {
        await apiClient.post(
          `/api/patterns/${patternId}/feedback`,
          { status },
          { params: { user_id: userId } }
        );
        setResolvedPatternIds((prev) => ({ ...prev, [patternId]: status }));
      } catch {
        setError("暂时无法保存反馈，请重试。");
      } finally {
        setPendingPatternId(null);
      }
    },
    [userId]
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = input.trim();
    if (!message || isSending) {
      return;
    }
    setInput("");
    setError(null);
    setIsSending(true);
    onAppendMessage({ role: "user", content: message });
    try {
      const response = await postChat({
        user_id: userId.trim() || "demo-user",
        conversation_id: conversationId,
        message
      });
      onReplaceLastResponse(response);
      onAppendMessage({ role: "assistant", content: response.assistant_response });
    } catch {
      setError("请求失败。请确认后端服务已启动，并且 VITE_API_BASE_URL 配置正确。");
    } finally {
      setIsSending(false);
    }
  }

  const riskLevel = lastResponse?.risk_level ?? "none";
  const riskClass = riskLevel === "high" || riskLevel === "medium" ? "is-alert" : "";

  return (
    <section className="page">
      <header className="page-header">
        <p className="eyebrow">成长对话</p>
        <h2>对话</h2>
      </header>
      <div className="disclaimer-panel">
        <p>
          本产品用于自我成长反思和日常行动规划，不提供医学诊断、心理治疗、危机干预或紧急救助。
          如果你正处于现实危险中，请立即联系当地紧急服务或身边可信任的人。
        </p>
      </div>

      <div className="chat-layout">
        <div className="chat-main">
          <div className="chat-thread" aria-live="polite">
            {messages.length === 0 ? (
              <p className="chat-placeholder">
                发送一条演示消息，运行完整的 LangGraph 工作流。
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
              用户
              <input value={userId} onChange={(event) => onChangeUserId(event.target.value)} />
            </label>
            <label className="chat-input">
              消息
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                rows={4}
              />
            </label>
            <button className="primary-button" type="submit" disabled={isSending || !input.trim()}>
              {isSending ? "发送中" : "发送"}
            </button>
          </form>
          {error ? <p className="chat-error">{error}</p> : null}
        </div>

        <aside className="chat-side-panel">
          <div>
            <p className="panel-label">回复策略</p>
            <strong>
              {labelFromMap(STRATEGY_LABELS, lastResponse?.strategy, "尚未开始")}
            </strong>
          </div>
          <div>
            <p className="panel-label">风险等级</p>
            <span className={`risk-badge ${riskClass}`}>
              {labelFromMap(RISK_LABELS, riskLevel, "无风险")}
            </span>
            {displayRiskReason(lastResponse?.risk_reason) ? (
              <p className="risk-reason">{displayRiskReason(lastResponse?.risk_reason)}</p>
            ) : null}
          </div>
          <div>
            <p className="panel-label">召回记忆</p>
            <strong>{lastResponse?.retrieved_memories.length ?? 0}</strong>
          </div>
          {lastResponse?.detected_patterns && lastResponse.detected_patterns.length > 0 ? (
            <div className="detected-patterns">
              <p className="panel-label">候选模式</p>
              {lastResponse.detected_patterns.map((pattern) => {
                const patternId = (pattern as Record<string, unknown>).pattern_id as string ?? "";
                const emotion = (pattern as Record<string, unknown>).emotion as string ?? "-";
                const trigger = (pattern as Record<string, unknown>).trigger as string ?? "-";
                const behavior = (pattern as Record<string, unknown>).behavior as string ?? "-";
                const result = (pattern as Record<string, unknown>).result as string ?? "-";
                const evidenceIds = (pattern as Record<string, unknown>).evidence_memory_ids as string[] ?? [];
                const status = (pattern as Record<string, unknown>).status as string ?? "detected";
                const resolvedStatus = resolvedPatternIds[patternId];
                const effectiveStatus = resolvedStatus ?? status;
                const isPending = pendingPatternId === patternId;
                const isResolved = effectiveStatus === "confirmed" || effectiveStatus === "rejected";
                return (
                  <article key={patternId} className="pattern-card">
                    <dl className="pattern-details">
                      <div><dt>触发</dt><dd>{trigger}</dd></div>
                      <div><dt>情绪</dt><dd>{emotion}</dd></div>
                      <div><dt>行为</dt><dd>{behavior}</dd></div>
                      <div><dt>结果</dt><dd>{result}</dd></div>
                    </dl>
                    <div className="pattern-evidence">
                      <span>证据记忆: {evidenceIds.length} 条</span>
                    </div>
                    {!isResolved ? (
                      <div className="pattern-actions">
                        <button
                          type="button"
                          className="primary-button"
                          disabled={isPending}
                          onClick={() => { void submitPatternFeedback(patternId, "confirmed"); }}
                        >
                          确认
                        </button>
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={isPending}
                          onClick={() => { void submitPatternFeedback(patternId, "rejected"); }}
                        >
                          拒绝
                        </button>
                      </div>
                    ) : (
                      <span className="pattern-status">
                        {effectiveStatus === "confirmed" ? "已确认" : "已拒绝"}
                      </span>
                    )}
                  </article>
                );
              })}
            </div>
          ) : null}
          {lastResponse?.generated_task ? (
            <div className="generated-task">
              <p className="panel-label">生成任务</p>
              <strong>{lastResponse.generated_task.task_content}</strong>
              <span>
                难度：{labelFromMap(DIFFICULTY_LABELS, lastResponse.generated_task.difficulty, "低")} ·{" "}
                时长：{lastResponse.generated_task.duration_minutes ?? 15} 分钟
              </span>
            </div>
          ) : null}
        </aside>
      </div>
    </section>
  );
}
