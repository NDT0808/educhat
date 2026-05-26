import { useEffect, useRef } from "react";
import type { Message } from "../types/chat";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

interface MessageListProps {
	messages: Message[];
	isLoading: boolean;
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
	const messagesEndRef = useRef<HTMLDivElement>(null);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages, isLoading]);

	return (
		<div className="flex-1 min-h-0 overflow-y-auto px-4 pt-6 pb-8 scroll-smooth bg-slate-50/50">
			<div className="max-w-4xl mx-auto space-y-5">
				{messages.map((message) => (
					<MessageBubble key={message.id} message={message} />
				))}

				{isLoading && (
					<div className="flex gap-4">
						<div className="flex-shrink-0 mt-1">
							<div className="w-9 h-9 rounded-md bg-white flex items-center justify-center border border-slate-200">
								<div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
							</div>
						</div>
						<div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
							<TypingIndicator />
						</div>
					</div>
				)}
				<div ref={messagesEndRef} className="h-4" />
			</div>
		</div>
	);
}
