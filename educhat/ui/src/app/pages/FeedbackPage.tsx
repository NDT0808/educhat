import React, { useState, useEffect } from "react";
import {
    Star,
    Send,
    CheckCircle2,
    AlertTriangle,
    Tag
} from "lucide-react";
import { apiService } from "../services/apiService";
import { useAuth } from "../context/AuthContext";
import { cn } from "../utils/cn";

const FeedbackPage: React.FC = () => {
    const { user } = useAuth();
    const [courses, setCourses] = useState<any[]>([]);
    const [selectedCourse, setSelectedCourse] = useState<number | null>(null);
    const [terms, setTerms] = useState<any[]>([]);
    const [selectedTerm, setSelectedTerm] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const [ratings, setRatings] = useState({
        workload: 3,
        materials: 3,
        practical: 3,
        fairness: 3,
        support: 3,
        overall: 3
    });
    const [tags, setSelectedTags] = useState<string[]>([]);
    const [comment, setComment] = useState("");

    const availableTags = ["Quá nặng", "Thi khó", "Thiếu thực hành", "Tài liệu tốt", "Giảng viên nhiệt tình", "Lý thuyết khô khan"];

    useEffect(() => {
        apiService.getCourses().then(res => setCourses(res.courses));
        apiService.getTerms().then(res => {
            setTerms(res.terms);
            if (res.terms.length > 0) setSelectedTerm(res.terms[0].id);
        });
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedCourse) return;

        setIsSubmitting(true);
        try {
            await apiService.submitFeedback({
                student_id: Number(user?.id) || 1,
                course_id: selectedCourse,
                term_id: selectedTerm,
                ...ratings,
                tags,
                comment
            });
            setSubmitted(true);
        } catch (err) {
            console.error(err);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (submitted) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[600px] text-center space-y-6">
                <div className="w-24 h-24 bg-green-50 text-green-600 rounded-full flex items-center justify-center animate-bounce">
                    <CheckCircle2 size={48} />
                </div>
                <h2 className="text-3xl font-black text-slate-900">Cảm ơn bạn!</h2>
                <p className="text-slate-500 font-medium max-w-sm">
                    Phản hồi của bạn đã được ghi nhận ẩn danh. Điều này giúp cộng đồng sinh viên chọn môn học hiệu quả hơn.
                </p>
                <button
                    onClick={() => { setSubmitted(false); setSelectedCourse(null); setComment(""); }}
                    className="px-8 py-3 bg-slate-900 text-white rounded-2xl font-bold shadow-xl hover:bg-slate-800 transition-all"
                >
                    Gửi đánh giá khác
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-12">
            <div className="text-center space-y-3">
                <h1 className="text-4xl font-black text-slate-900">Course Feedback</h1>
                <p className="text-slate-500 font-bold flex items-center justify-center gap-2">
                    <AlertTriangle size={18} className="text-orange-400" />
                    Hoàn toàn ẩn danh • Chia sẻ thật để giúp bạn bè
                </p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-[40px] p-8 sm:p-12 border border-slate-100 shadow-2xl shadow-slate-200/50 space-y-10">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                    <div className="space-y-3">
                        <label className="text-sm font-black text-slate-700 ml-1">Chọn học kỳ</label>
                        <select
                            value={selectedTerm}
                            onChange={(e) => setSelectedTerm(e.target.value)}
                            className="w-full bg-slate-50 border border-slate-100 rounded-2xl px-5 py-4 font-bold text-slate-700 outline-none focus:ring-4 focus:ring-blue-50 transition-all appearance-none"
                        >
                            {terms.map(term => <option key={term.id} value={term.id}>{term.name}</option>)}
                        </select>
                    </div>

                    <div className="space-y-3">
                        <label className="text-sm font-black text-slate-700 ml-1">Chọn môn học</label>
                        <select
                            value={selectedCourse || ""}
                            onChange={(e) => setSelectedCourse(parseInt(e.target.value))}
                            required
                            className="w-full bg-slate-50 border border-slate-100 rounded-2xl px-5 py-4 font-bold text-slate-700 outline-none focus:ring-4 focus:ring-blue-50 transition-all appearance-none text-ellipsis"
                        >
                            <option value="">-- Mời chọn môn --</option>
                            {courses.map(course => <option key={course.course_code} value={1}>{course.name} ({course.course_code})</option>)}
                        </select>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-12 gap-y-10">
                    {[
                        { label: "Khối lượng công việc (Workload)", key: "workload" },
                        { label: "Chất lượng tài liệu", key: "materials" },
                        { label: "Tính thực tiễn", key: "practical" },
                        { label: "Sự công bằng (Đánh giá)", key: "fairness" },
                        { label: "Hỗ trợ từ giảng viên", key: "support" },
                        { label: "Đánh giá chung", key: "overall" }
                    ].map(metric => (
                        <div key={metric.key} className="space-y-4">
                            <label className="text-sm font-bold text-slate-700 flex justify-between">
                                <span>{metric.label}</span>
                                <span className="text-blue-600">{(ratings as any)[metric.key]}/5</span>
                            </label>
                            <div className="flex items-center gap-2">
                                {[1, 2, 3, 4, 5].map(star => (
                                    <button
                                        key={star}
                                        type="button"
                                        onClick={() => setRatings({ ...ratings, [metric.key]: star })}
                                        className={cn(
                                            "p-1 transition-transform active:scale-90",
                                            star <= (ratings as any)[metric.key] ? "text-amber-400" : "text-slate-200"
                                        )}
                                    >
                                        <Star size={24} fill={star <= (ratings as any)[metric.key] ? "currentColor" : "none"} />
                                    </button>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="space-y-4">
                    <label className="text-sm font-black text-slate-700 ml-1">Tags phổ biến</label>
                    <div className="flex flex-wrap gap-2">
                        {availableTags.map(tag => (
                            <button
                                key={tag}
                                type="button"
                                onClick={() => {
                                    const newTags = tags.includes(tag) ? tags.filter(t => t !== tag) : [...tags, tag];
                                    setSelectedTags(newTags);
                                }}
                                className={cn(
                                    "px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center gap-2",
                                    tags.includes(tag)
                                        ? "bg-blue-600 border-blue-600 text-white"
                                        : "bg-white border-slate-100 text-slate-500 hover:border-slate-200"
                                )}
                            >
                                <Tag size={12} />
                                {tag}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="space-y-4">
                    <label className="text-sm font-black text-slate-700 ml-1">Nhận xét thêm (Optional)</label>
                    <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-100 rounded-3xl px-6 py-4 font-medium text-slate-700 outline-none focus:ring-4 focus:ring-blue-50 transition-all min-h-[120px]"
                        placeholder="Bạn thấy môn này thế nào? Có tip gì để qua môn không?..."
                    />
                </div>

                <button
                    type="submit"
                    disabled={isSubmitting || !selectedCourse}
                    className="w-full py-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-3xl font-black text-xl shadow-2xl shadow-blue-200 hover:scale-[1.01] active:scale-[0.98] transition-all disabled:opacity-50 disabled:scale-100 flex items-center justify-center gap-3"
                >
                    {isSubmitting ? (
                        <div className="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        <>
                            <Send size={24} />
                            <span>Gửi đánh giá ẩn danh</span>
                        </>
                    )}
                </button>
            </form>
        </div>
    );
};

export default FeedbackPage;
