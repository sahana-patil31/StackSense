export interface AssistantSource {
  source_type: string;
  source_id: string | null;
  title: string;
}

export interface AssistantChatResponse {
  answer: string;
  sources: AssistantSource[];
  confidence: number;
  conversation_id: string;
}

export interface AssistantMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: AssistantSource[];
}