import { Message } from "../types/chat";
import api from "./api";

export interface ChatResponse {
  status: string;
  answer: string;
  emotion?: string;
}

export const apiService = {
  sendMessage: async (message: Message[]): Promise<ChatResponse> => {
    const response = await api.post("/v1/chat", {
      messages: message.map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
    });
    if (!(response as any).ok) throw new Error("Failed to send message");
    return response.data;
  },

  optimizeSchedule: async (
    courses: string[],
    constraints: string[]
  ): Promise<any> => {
    const response = await api.post("/v1/optimize_schedule", {
      courses,
      constraints,
    });
    if (!(response as any).ok) throw new Error("Failed to optimize schedule");
    return response.data;
  },

  getCourses: async (): Promise<any> => {
    const response = await api.get("/v1/courses");
    return response.data;
  },

  getAvailableCourses: async (): Promise<any> => {
    const response = await api.get("/v1/courses");
    return response.data;
  },

  extractConstraints: async (text: string): Promise<any> => {
    const response = await api.post("/v1/extract_constraints", { text });
    return response.data;
  },

  getCurriculum: async (): Promise<any> => {
    const response = await api.get("/v1/curriculum");
    return response.data;
  },

  getFullCurriculum: async (): Promise<any> => {
    const response = await api.get("/v1/curriculum/full");
    return response.data;
  },

  // --- Academic Features ---

  getTerms: async (): Promise<any> => {
    const response = await api.get("/v1/terms");
    return response.data;
  },

  generatePlans: async (request: any): Promise<any> => {
    const response = await api.post("/v1/planner/generate_plans", request);
    return response.data;
  },

  checkRegistration: async (request: any): Promise<any> => {
    const response = await api.post("/v1/registration/check", request);
    return response.data;
  },

  submitFeedback: async (request: any): Promise<any> => {
    const response = await api.post("/v1/feedback/submit", request);
    return response.data;
  },

  getFeedbackHeatmap: async (termId: string, courseId?: number): Promise<any> => {
    const response = await api.get("/v1/feedback/heatmap", {
      params: { term_id: termId, course_id: courseId }
    });
    return response.data;
  },

  applyPlan: async (studentId: number, termId: string, offeringIds: number[]): Promise<any> => {
    const response = await api.post("/v1/registration/apply", {
      student_id: studentId,
      term_id: termId,
      offering_ids: offeringIds
    });
    return response.data;
  },

  getCalendarIcsUrl: (studentId: number, termId: string): string => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
    return `${BASE_URL}/v1/calendar/ics?student_id=${studentId}&term_id=${termId}`;
  },

  getTimetable: async (termId: string): Promise<any> => {
    const response = await api.get("/v1/timetable", {
      params: { term_id: termId }
    });
    return response.data;
  },

  // --- OCR Features ---
  scanOCRImage: async (imageFile: File): Promise<any> => {
    const formData = new FormData();
    formData.append("file", imageFile);
    
    // Gọi thẳng sang OCR Microservice chạy ở cổng 8002
    const response = await fetch("http://localhost:8002/v1/ocr/scan", {
      method: "POST",
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error("Lỗi khi kết nối tới OCR Microservice");
    }
    
    return await response.json();
  }
};
