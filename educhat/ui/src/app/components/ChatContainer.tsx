import { useState, useEffect } from "react";
import { sendMessage } from "../services/chatService";
import { apiService } from "../services/apiService";
import type { Message } from "../types/chat";
import { generateUUID } from "../utils/uuid";
import ChatHeader from "./ChatHeader";
import ChatInput from "./ChatInput";
import MessageList from "./MessageList";
import SuggestedQuestions from "./SuggestedQuestions";
import ScheduleOptimizerModal from "./ScheduleOptimizerModal";

export default function ChatContainer() {
	const [messages, setMessages] = useState<Message[]>([]);
	const [isLoading, setIsLoading] = useState(false);
	const [isOptimizerOpen, setIsOptimizerOpen] = useState(false);
	const [optimizerData, setOptimizerData] = useState<{ courses: string[], constraints: string[] } | null>(null);

	// Listen for custom event from CourseSelectionBubble to open results
	useEffect(() => {
		const handleOpenResults = (e: CustomEvent) => {
			if (e.detail) {
				setOptimizerData({
					courses: e.detail.courses || [],
					constraints: e.detail.constraints || []
				});
				setIsOptimizerOpen(true);
			}
		};
		window.addEventListener('openOptimizerResults', handleOpenResults as EventListener);
		return () => window.removeEventListener('openOptimizerResults', handleOpenResults as EventListener);
	}, []);

	const handleReset = async () => {
		setIsLoading(true);
		try {
			setMessages([]);
			setOptimizerData(null);
		} catch (error) {
			console.error("Error resetting session:", error);
		} finally {
			setIsLoading(false);
		}
	};

	const handleOptimizeClick = () => {
		handleSendMessage("Hãy giúp tôi sắp xếp thời khóa biểu");
	};

	const handleSendMessage = async (content: string) => {
		// Add user message to state immediately for UX
		const userMsg: Message = {
			id: generateUUID(),
			role: "user",
			content,
		};
		setMessages((prev) => [...prev, userMsg]);
		setIsLoading(true);

		// Check for schedule optimization intent (robust keyword check)
		// We normalize by removing accents just for the check if possible, or check multiple variants
		// Since we don't have a heavy library here, we'll check common variants
		const lowerContent = content.toLowerCase();
		const isIntent =
			lowerContent.includes("sắp xếp") || lowerContent.includes("sap xep") ||
			lowerContent.includes("thời khóa biểu") || lowerContent.includes("thoi khoa bieu") ||
			lowerContent.includes("tkb") ||
			lowerContent.includes("schedule") ||
			lowerContent.includes("lịch học");

		if (isIntent) {
			try {
				// Extract constraints
				const { constraints } = await apiService.extractConstraints(content);

				const assistantMsg: Message = {
					id: generateUUID(),
					role: "assistant",
					content: "Dưới đây là công cụ chọn môn học dựa trên yêu cầu của bạn. Vui lòng chọn môn và tôi sẽ tìm lịch tối ưu:",
					interactiveData: {
						type: "schedule_optimizer",
						constraints: constraints || []
					}
				};

				setTimeout(() => {
					setMessages((prev) => [...prev, assistantMsg]);
					setIsLoading(false);
				}, 600);
				return;
			} catch (e) {
				console.error("Constraint extraction failed", e);
			}
		}

		try {
			const { answer, emotion } = await sendMessage(
				[...messages, userMsg],
			);
			const assistantMsg: Message = {
				id: generateUUID(),
				role: "assistant",
				content: answer,
				emotion: emotion,
			};
			setMessages((prev) => [...prev, assistantMsg]);
		} catch (error) {
			// ... error handling
			console.error(error);
			setIsLoading(false);
		} finally {
			setIsLoading(false);
		}
	};

	const handleQuestionClick = (question: string) => {
		handleSendMessage(question);
	};

	return (
		<div className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
			<ChatHeader
				onReset={handleReset}
				onOptimize={handleOptimizeClick}
			/>
			{messages.length === 0 && !isLoading ? (
				<SuggestedQuestions onQuestionClick={handleQuestionClick} />
			) : (
				<MessageList messages={messages} isLoading={isLoading} />
			)}
			<ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />

			<ScheduleOptimizerModal
				isOpen={isOptimizerOpen}
				onClose={() => setIsOptimizerOpen(false)}
				initialCourses={optimizerData?.courses}
				initialConstraints={optimizerData?.constraints}
			/>
		</div>
	);
}
