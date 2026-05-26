import { Bot, User } from "lucide-react";
import Markdown from "react-markdown";
import { motion } from "motion/react";
import type { Message } from "../types/chat";
import CourseSelectionBubble from "./CourseSelectionBubble";
import { cn } from "../utils/cn";


interface MessageBubbleProps {
	message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
	const isUser = message.role === "user";

	return (
		<motion.div
			initial={{ opacity: 0, y: 10, scale: 0.95 }}
			animate={{ opacity: 1, y: 0, scale: 1 }}
			transition={{ duration: 0.3, ease: "easeOut" }}
			className={cn(
				"flex gap-4 group",
				isUser ? "flex-row-reverse" : "flex-row"
			)}
		>
			<div className="flex-shrink-0 mt-1">
				<div
					className={cn(
						"w-9 h-9 rounded-md flex items-center justify-center border transition-colors",
						isUser
							? "bg-slate-900 text-white border-slate-900"
							: "bg-white text-slate-700 border-slate-200"
					)}
				>
					{isUser ? <User size={17} /> : <Bot size={18} />}
				</div>
			</div>

			<div className={cn(
				"flex flex-col max-w-[85%] sm:max-w-[75%] md:max-w-[70%]",
				isUser ? "items-end" : "items-start"
			)}>
				<div className="flex items-center gap-2 mb-1 px-1">
					<span className="text-xs font-medium text-slate-500">
						{isUser ? "Bạn" : "EduChat Assistant"}
					</span>
				</div>

				<div
					className={cn(
						"rounded-lg px-4 py-3 border text-[15px] leading-relaxed",
						isUser
							? "bg-slate-900 text-white border-slate-900"
							: "bg-white text-slate-800 border-slate-200"
					)}
				>
					{isUser ? (
						<p className="whitespace-pre-wrap break-words">{message.content}</p>
					) : (
						<div className="prose prose-sm max-w-none 
							prose-p:my-1.5 prose-p:leading-relaxed 
							prose-headings:text-gray-900 prose-headings:font-bold prose-headings:my-2
							prose-strong:text-gray-900 prose-strong:font-semibold
							prose-ul:text-gray-800 prose-ul:my-2 prose-li:my-0.5
							prose-ol:text-gray-800 
							prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
							prose-code:px-1.5 prose-code:py-0.5 prose-code:bg-gray-100 prose-code:rounded-md prose-code:text-gray-800 prose-code:font-mono prose-code:text-xs prose-code:before:content-none prose-code:after:content-none
							prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:rounded-xl prose-pre:p-4
							prose-table:border-collapse prose-table:w-full prose-table:my-2
							prose-th:bg-gray-50 prose-th:p-2 prose-th:text-xs prose-th:uppercase prose-th:text-gray-500 prose-th:font-semibold prose-th:border prose-th:border-gray-200
							prose-td:p-2 prose-td:text-sm prose-td:border prose-td:border-gray-200"
						>
							<Markdown
								components={{
									ul: ({ node, ...props }) => (
										<ul {...props} className="list-disc pl-5 my-2 space-y-1 marker:text-gray-400" />
									),
									ol: ({ node, ...props }) => (
										<ol
											{...props}
											className="list-decimal pl-5 my-2 space-y-1 marker:text-gray-400"
										/>
									),
									li: ({ node, ...props }) => (
										<li {...props} className="pl-1" />
									),
									table: ({ node, ...props }) => (
										<div className="overflow-x-auto my-4 rounded-lg border border-gray-200 shadow-sm">
											<table {...props} className="min-w-full divide-y divide-gray-200" />
										</div>
									),
									thead: ({ node, ...props }) => (
										<thead {...props} className="bg-gray-50/50" />
									),
									// Custom components rendering if needed
								}}
							>
								{message.content}
							</Markdown>

							{/* Interactive Content */}
							{message.interactiveData?.type === "schedule_optimizer" && (
								<motion.div
									initial={{ opacity: 0, y: 10 }}
									animate={{ opacity: 1, y: 0 }}
									transition={{ delay: 0.2 }}
									className="mt-4 -mx-2 sm:-mx-4"
								>
									<CourseSelectionBubble
										initialConstraints={message.interactiveData.constraints}
										onOptimize={(courses, constraints) => {
											const event = new CustomEvent('openOptimizerResults', {
												detail: { courses, constraints }
											});
											window.dispatchEvent(event);
										}}
									/>
								</motion.div>
							)}
						</div>
					)}
				</div>
			</div>
		</motion.div>
	);
}
