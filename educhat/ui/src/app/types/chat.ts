export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  interactiveData?: {
    type: "schedule_optimizer";
    constraints: string[];
  };
  emotion?: string;
}

export interface ChatConfig {
  apiMode: "mock" | "api";
  baseUrl: string;
}
