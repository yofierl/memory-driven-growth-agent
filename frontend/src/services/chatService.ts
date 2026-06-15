import { apiClient } from "../api/client";

export type ChatRequest = {
  user_id: string;
  conversation_id?: string;
  message: string;
};

export type ChatResponse = {
  conversation_id: string;
  assistant_response: string;
  strategy: string;
  risk_level: string;
  risk_reason?: string | null;
  safety_handled: boolean;
  retrieved_memories: Record<string, unknown>[];
  detected_patterns: Record<string, unknown>[];
  generated_task?: {
    task_content?: string;
    difficulty?: string;
    duration_minutes?: number;
    method_id?: string;
    status?: string;
  } | null;
};

export async function postChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>("/api/chat", request);
  return response.data;
}
