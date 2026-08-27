import axios from 'axios';
import type { AssistantChatResponse } from '../types/assistant';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const chatWithAssistant = async (
  question: string,
  repositoryId: string,
  conversationId?: string
): Promise<AssistantChatResponse> => {
  const response = await api.post<AssistantChatResponse>('/api/assistant/chat', {
    question,
    repository_id: repositoryId,
    ...(conversationId ? { conversation_id: conversationId } : {}),
  });
  return response.data;
};