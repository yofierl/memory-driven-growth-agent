import { useEffect, useMemo, useState } from "react";

import { apiClient } from "../api/client";

type PatternStatus = "detected" | "confirmed" | "rejected";

type PatternItem = {
  pattern_id: string;
  user_id: string;
  scenario?: string | null;
  trigger?: string | null;
  emotion?: string | null;
  behavior?: string | null;
  result?: string | null;
  frequency?: number | null;
  evidence_memory_ids: string[];
  confidence?: number | null;
  status: PatternStatus;
};

const DEMO_USER_ID = "user-1";

export function PatternPage() {
  const [patterns, setPatterns] = useState<PatternItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingPatternId, setPendingPatternId] = useState<string | null>(null);

  async function loadPatterns() {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<{ patterns: PatternItem[] }>("/api/patterns", {
        params: { user_id: DEMO_USER_ID }
      });
      setPatterns(response.data.patterns);
    } catch (loadError) {
      setError("Unable to load pattern candidates right now.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPatterns();
  }, []);

  async function submitFeedback(patternId: string, status: Extract<PatternStatus, "confirmed" | "rejected">) {
    setPendingPatternId(patternId);
    setError(null);
    try {
      await apiClient.post(`/api/patterns/${patternId}/feedback`, { status }, {
        params: { user_id: DEMO_USER_ID }
      });
      setPatterns((current) =>
        current
          .map((item) => (item.pattern_id === patternId ? { ...item, status } : item))
          .filter((item) => item.status !== "rejected")
      );
    } catch {
      setError("Unable to save your feedback right now.");
    } finally {
      setPendingPatternId(null);
    }
  }

  const hasPatterns = useMemo(() => patterns.length > 0, [patterns]);

  return (
    <section className="page">
      <header className="page-header">
        <p className="eyebrow">Evidence loop</p>
        <h2>Pattern</h2>
      </header>

      <div className="pattern-toolbar">
        <p>Candidate patterns require at least three evidence memories before they appear here.</p>
        <button type="button" className="secondary-button" onClick={() => void loadPatterns()}>
          Refresh
        </button>
      </div>

      {loading ? <div className="empty-panel"><p>Loading pattern candidates...</p></div> : null}
      {!loading && error ? <div className="empty-panel"><p>{error}</p></div> : null}
      {!loading && !error && !hasPatterns ? (
        <div className="empty-panel">
          <p>No detected or confirmed behavior patterns yet.</p>
        </div>
      ) : null}

      {!loading && !error && hasPatterns ? (
        <div className="pattern-grid">
          {patterns.map((pattern) => {
            const disabled = pendingPatternId === pattern.pattern_id;
            return (
              <article key={pattern.pattern_id} className="pattern-card">
                <div className="pattern-card-header">
                  <div>
                    <p className="pattern-status">{pattern.status}</p>
                    <h3>{pattern.scenario ?? "General scenario"}</h3>
                  </div>
                  <div className="pattern-meta">
                    <span>frequency {pattern.frequency ?? pattern.evidence_memory_ids.length}</span>
                    <span>confidence {Math.round((pattern.confidence ?? 0) * 100)}%</span>
                  </div>
                </div>

                <dl className="pattern-details">
                  <div>
                    <dt>Trigger</dt>
                    <dd>{pattern.trigger ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Emotion</dt>
                    <dd>{pattern.emotion ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Behavior</dt>
                    <dd>{pattern.behavior ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Result</dt>
                    <dd>{pattern.result ?? "-"}</dd>
                  </div>
                </dl>

                <div className="pattern-evidence">
                  <p>Evidence memory IDs</p>
                  <ul>
                    {pattern.evidence_memory_ids.map((memoryId) => (
                      <li key={memoryId}>{memoryId}</li>
                    ))}
                  </ul>
                </div>

                {pattern.status === "detected" ? (
                  <div className="pattern-actions">
                    <button
                      type="button"
                      className="primary-button"
                      disabled={disabled}
                      onClick={() => void submitFeedback(pattern.pattern_id, "confirmed")}
                    >
                      Confirm
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={disabled}
                      onClick={() => void submitFeedback(pattern.pattern_id, "rejected")}
                    >
                      Reject
                    </button>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
