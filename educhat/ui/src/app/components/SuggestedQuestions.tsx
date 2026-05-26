import { ArrowRight, BookOpen, CalendarDays, GraduationCap, Search } from "lucide-react";
import { uuidv7 } from "uuidv7";
import { motion } from "motion/react";


interface SuggestedQuestionsProps {
	onQuestionClick: (question: string) => void;
}

const SUGGESTED_QUESTIONS = [
	{ icon: Search, text: "Đại Học Quốc Gia Thành Phố Hồ Chí Minh năm 2025" },
	{ icon: GraduationCap, text: "Các tổ hợp xét tuyển của Trường Đại học Công nghệ Thông tin - ĐH Quốc gia TP.HCM 2025?" },
	{ icon: BookOpen, text: "Trường Đại học Quốc gia Thành Phố Hồ Chí Minh có những phương thức xét tuyển nào năm 2025?" },
	{ icon: CalendarDays, text: "Hãy giúp tôi sắp xếp thời khóa biểu học kỳ này" },
];

export default function SuggestedQuestions({
	onQuestionClick,
}: SuggestedQuestionsProps) {
	return (
		<div className="flex-1 min-h-0 overflow-y-auto bg-slate-50/50 px-4 py-8">
			<motion.div
				initial={{ opacity: 0, y: 20 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 0.5 }}
				className="max-w-4xl w-full mx-auto"
			>
				<div className="mb-8">
					<div className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 mb-4">
						<span className="h-2 w-2 rounded-full bg-emerald-500" />
						Sẵn sàng hỗ trợ
					</div>
					<h2 className="text-2xl sm:text-3xl font-semibold text-slate-950 mb-3 tracking-tight">
						Bạn cần tra cứu hay lập kế hoạch học tập?
					</h2>
					<p className="text-slate-500 text-base max-w-2xl">
						Chọn một câu hỏi dưới đây hoặc nhập câu hỏi để bắt đầu
					</p>
				</div>

				<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
					{SUGGESTED_QUESTIONS.map((question, index) => {
						const Icon = question.icon;
						return (
						<motion.button
							initial={{ opacity: 0, x: -20 }}
							animate={{ opacity: 1, x: 0 }}
							transition={{ delay: index * 0.1 + 0.3 }}
							type="button"
							key={uuidv7()}
							onClick={() => onQuestionClick(question.text)}
							className="text-left p-4 rounded-lg border border-slate-200 bg-white hover:border-slate-400 transition-colors group"
						>
							<div className="flex items-start gap-3">
								<div className="flex-shrink-0 w-9 h-9 rounded-md bg-slate-100 text-slate-600 flex items-center justify-center group-hover:bg-slate-900 group-hover:text-white transition-colors">
									<Icon size={18} />
								</div>
								<p className="flex-1 text-slate-700 font-medium group-hover:text-slate-950 transition-colors line-clamp-2">
									{question.text}
								</p>
								<ArrowRight className="w-5 h-5 text-slate-300 group-hover:text-slate-700 group-hover:translate-x-1 transition-all" />
							</div>
						</motion.button>
					)})}
				</div>
			</motion.div>
		</div>
	);
}
