import { Bot, Eraser, Calendar } from "lucide-react";

interface ChatHeaderProps {
	onReset?: () => void;
	onOptimize?: () => void;
}

export default function ChatHeader({ onReset, onOptimize }: ChatHeaderProps) {
	return (
		<div className="border-b border-slate-200 bg-white px-4 sm:px-6 py-3 flex items-center justify-between">
			<div className="flex min-w-0 items-center gap-3">
				<div className="w-9 h-9 shrink-0 rounded-md bg-slate-900 flex items-center justify-center text-white">
					<Bot size={19} />
				</div>
				<div className="min-w-0">
					<h1 className="truncate text-base font-semibold text-slate-900 tracking-tight">
						EduChat Assistant
					</h1>
					<p className="truncate text-xs font-medium text-slate-500">Tư vấn tuyển sinh, môn học và lịch học</p>
				</div>

			</div>

			<div className="flex shrink-0 items-center gap-2">
				<button
					type="button"
					onClick={onOptimize}
					className="px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-200 rounded-md hover:bg-slate-50 transition-colors flex items-center gap-2"
				>
					<Calendar size={16} strokeWidth={2.5} />
					<span className="hidden sm:inline">Sắp xếp TKB</span>
				</button>

				<div className="w-px h-6 bg-slate-200 mx-1" />

				<button
					type="button"
					onClick={onReset}
					className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
					title="Làm mới cuộc trò chuyện"
				>
					<Eraser size={20} />
				</button>
			</div>
		</div>
	);
}
