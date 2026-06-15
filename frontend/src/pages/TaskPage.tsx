import { useEffect, useMemo, useState } from "react";

import { apiClient } from "../api/client";

type TaskStatus = "pending" | "completed" | "failed" | "adjusted";

type TaskItem = {
  task_id: string;
  user_id: string;
  task_content: string;
  status: TaskStatus;
  method_id?: string | null;
  feedback?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

const DEMO_USER_ID = "user-1";

export function TaskPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingTaskId, setPendingTaskId] = useState<string | null>(null);

  async function loadTasks() {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<{ tasks: TaskItem[] }>("/api/tasks", {
        params: { user_id: DEMO_USER_ID }
      });
      setTasks(response.data.tasks);
    } catch {
      setError("Unable to load action tasks right now.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTasks();
  }, []);

  async function updateTask(taskId: string, status: "completed" | "failed") {
    const feedback = status === "failed" ? "这次任务还是偏难，下一次希望再小一步。" : undefined;
    setPendingTaskId(taskId);
    setError(null);
    try {
      await apiClient.post(
        `/api/tasks/${taskId}/status`,
        { status, feedback },
        { params: { user_id: DEMO_USER_ID } }
      );
      setTasks((current) =>
        current.map((task) =>
          task.task_id === taskId
            ? { ...task, status, feedback: feedback ?? task.feedback }
            : task
        )
      );
    } catch {
      setError("Unable to save task feedback right now.");
    } finally {
      setPendingTaskId(null);
    }
  }

  const hasTasks = useMemo(() => tasks.length > 0, [tasks]);

  return (
    <section className="page">
      <header className="page-header">
        <p className="eyebrow">Action loop</p>
        <h2>Task</h2>
      </header>

      <div className="task-toolbar">
        <p>Confirmed patterns can route into one lightweight 15-30 minute action task.</p>
        <button type="button" className="secondary-button" onClick={() => void loadTasks()}>
          Refresh
        </button>
      </div>

      {loading ? <div className="empty-panel"><p>Loading tasks...</p></div> : null}
      {!loading && error ? <div className="empty-panel"><p>{error}</p></div> : null}
      {!loading && !error && !hasTasks ? (
        <div className="empty-panel">
          <p>No generated action tasks yet.</p>
        </div>
      ) : null}

      {!loading && !error && hasTasks ? (
        <div className="task-grid">
          {tasks.map((task) => {
            const disabled = pendingTaskId === task.task_id;
            return (
              <article key={task.task_id} className="task-card">
                <div className="task-card-header">
                  <div>
                    <p className="pattern-status">{task.status}</p>
                    <h3>{task.task_content}</h3>
                  </div>
                  <div className="pattern-meta">
                    <span>{task.method_id ?? "no-method"}</span>
                  </div>
                </div>

                {task.feedback ? (
                  <div className="task-feedback">
                    <p>Latest feedback</p>
                    <span>{task.feedback}</span>
                  </div>
                ) : null}

                {task.status === "pending" ? (
                  <div className="pattern-actions">
                    <button
                      type="button"
                      className="primary-button"
                      disabled={disabled}
                      onClick={() => void updateTask(task.task_id, "completed")}
                    >
                      Mark completed
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={disabled}
                      onClick={() => void updateTask(task.task_id, "failed")}
                    >
                      Too hard this time
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
