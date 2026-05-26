import OpenAI from "openai";
import type { ChatConfig, Message } from "../types/chat";
import { apiService } from "./apiService";

export const config: ChatConfig & {
  usePublicLLM: boolean;
  openAiApiKey: string;
} = {
  apiMode: (import.meta.env.VITE_API_MODE as "mock" | "api") || "mock",
  baseUrl: import.meta.env.VITE_API_BASE_URL || "",
  usePublicLLM: import.meta.env.VITE_USING_PUBLIC_LLM === "true",
  openAiApiKey: import.meta.env.VITE_OPENAI_API_KEY || "",
};

const SYSTEM_PROMPT = `Bạn là một chuyên gia tư vấn tuyển sinh đại học.

NGUYÊN TẮC HOẠT ĐỘNG:
1. NGÔN NGỮ: Luôn trả lời bằng Tiếng Việt.
2. VAI TRÒ: Đóng vai là một tư vấn viên tuyển sinh chuyên nghiệp, thân thiện.
3. PHONG CÁCH: Trả lời ngắn gọn, súc tích, tập trung vào trọng tâm câu hỏi.
4. THỜI GIAN: Nếu người dùng không đề cập đến năm tuyển sinh, MẶC ĐỊNH là năm 2025.
5. XỬ LÝ CÂU HỎI:
   - KHÔNG quá khắt khe với đầu vào. Nếu câu hỏi chung chung nhưng vẫn hiểu được ý định, hãy trả lời đầy đủ dựa trên thông tin phổ biến nhất.
   - CHỈ hỏi lại nếu câu hỏi quá mơ hồ không thể đoán được ý định.
   - Nếu cần thêm thông tin từ người dùng để trả lời chính xác hơn, hãy đưa ra câu trả lời sơ bộ TRƯỚC, sau đó gợi ý danh sách các câu hỏi chi tiết ở cuối câu trả lời để người dùng chọn.`;

let client: OpenAI | null = null;

if (config.usePublicLLM && config.openAiApiKey) {
  client = new OpenAI({
    apiKey: config.openAiApiKey,
    dangerouslyAllowBrowser: true,
  });
}

const callOpenAI = async (messages: Message[]): Promise<string> => {
  try {
    if (!client) {
      throw new Error("OpenAI client not initialized");
    }
    const response = await client.chat.completions.create({
      model: import.meta.env.VITE_GPT_MODEL || "gpt-5.2-chat-latest",
      messages: [
        {
          role: "developer",
          content: SYSTEM_PROMPT,
        },
        ...messages.map((msg) => ({
          role:
            msg.role === "user" ? ("user" as const) : ("assistant" as const),
          content: msg.content,
        })),
      ],
    });

    return response.choices[0]?.message?.content || "";
  } catch (error) {
    console.error("OpenAI Error:", error);
    throw error;
  }
};

export const sendMessage = async (messages: Message[]): Promise<{answer: string, emotion?: string}> => {
  if (config.apiMode === "mock") {
    // Simulate 3-second delay
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // Return mock response
    const mockResponses = [
      "Cảm ơn bạn đã quan tâm đến chương trình tuyển sinh của trường! Tôi sẽ cung cấp thông tin chi tiết về vấn đề bạn đang quan tâm.",
      "Điểm chuẩn thường được công bố vào tháng 8 hàng năm. Bạn có thể xem thông tin chi tiết trên trang web chính thức của trường.",
      "Hồ sơ đăng ký cần bao gồm: Giấy chứng nhận tốt nghiệp THPT, Bằng tốt nghiệp THPT, Giấy khai sinh, CMND/CCCD, và các giấy tờ liên quan khác.",
      "Trường có nhiều ngành học đa dạng từ công nghệ thông tin, kinh tế, đến khoa học xã hội. Bạn quan tâm đến ngành nào?",
    ];

    return { answer: mockResponses[Math.floor(Math.random() * mockResponses.length)] };
  } else {
    // API mode

    if (config.usePublicLLM) return { answer: await callOpenAI(messages) };
    try {
      const data = await apiService.sendMessage(messages);
      return { answer: data.answer || "", emotion: data.emotion };
    } catch (error) {
      console.error("API Error:", error);
      throw error;
    }
  }
};
