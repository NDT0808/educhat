import React, { useState, useEffect } from "react";
import {
    Sparkles,
    Calendar,
    Clock,
    CheckCircle2,
    AlertCircle,
    ChevronRight,
    Filter,
    Coffee
} from "lucide-react";
import { apiService } from "../services/apiService";
import { cn } from "../utils/cn";
import { useAuth } from "../context/AuthContext";
import { NLRegistrationPanel } from "../components/NLRegistrationPanel";

const PlannerPage: React.FC = () => {
    const { user } = useAuth();
    const [terms, setTerms] = useState<any[]>([]);
    const [selectedTerm, setSelectedTerm] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [plans, setPlans] = useState<any[]>([]);
    const [registrationResult, setRegistrationResult] = useState<any>(null);
    const [previewingPlan, setPreviewingPlan] = useState<any | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [preferences, setPreferences] = useState({
        min_credits: 3,
        max_credits: 25,
        avoid_days: [] as string[],
        compact_days: false,
        prefer_morning: false
    });

    const [curriculum, setCurriculum] = useState<any>(null);

    useEffect(() => {
        // Fetch Terms
        apiService.getTerms().then(res => {
            setTerms(res.terms);
            if (res.terms.length > 0) setSelectedTerm(res.terms[0].id);
        }).catch(console.error);

        // Fetch Curriculum Strategy
        apiService.getCurriculum().then(res => {
            if (res.status === 'success') {
                setCurriculum(res.strategy);
            }
        }).catch(console.error);
    }, []);

    // ... handleGenerate ...



    const handleGenerate = async () => {
        setIsGenerating(true);
        setError(null);
        setPlans([]);
        try {
            const res = await apiService.generatePlans({
                student_id: Number(user?.id) || 1,
                term_id: selectedTerm,
                min_credits: preferences.min_credits,
                max_credits: preferences.max_credits,
                preferences: {
                    avoid_days: preferences.avoid_days,
                    compact_days: preferences.compact_days,
                    prefer_morning: preferences.prefer_morning
                }
            });
            if (res.plans && res.plans.length > 0) {
                setPlans(res.plans);
            } else {
                setError("Không tìm thấy kế hoạch phù hợp. Thử điều chỉnh tín chỉ hoặc sở thích.");
            }
        } catch (err: any) {
            console.error("Generate plans error:", err);
            setError(err?.response?.data?.detail || err?.message || "Lỗi kết nối server. Vui lòng đăng nhập lại.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleApplyPlan = async (plan: any) => {
        try {
            const res = await apiService.applyPlan(
                Number(user?.id) || 1,
                selectedTerm,
                plan.offering_ids
            );
            setRegistrationResult(res);
        } catch (err) {
            console.error(err);
            setRegistrationResult({ status: "error", message: "Đăng ký thất bại. Vui lòng thử lại." });
        }
    };

    return (
        <div className="space-y-8 max-w-6xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Registration Planner</h1>
                    <p className="text-slate-500 font-medium">Lập kế hoạch học tập thông minh dựa trên sở thích và tín chỉ.</p>
                </div>

                <div className="flex items-center gap-4 bg-white p-2 rounded-2xl border border-slate-100 shadow-sm">
                    {terms.map(term => (
                        <button
                            key={term.id}
                            onClick={() => setSelectedTerm(term.id)}
                            className={cn(
                                "px-4 py-2 rounded-xl text-sm font-bold transition-all",
                                selectedTerm === term.id
                                    ? "bg-blue-600 text-white shadow-lg shadow-blue-200"
                                    : "text-slate-600 hover:bg-slate-50"
                            )}
                        >
                            {term.name}
                        </button>
                    ))}
                </div>
            </div>

            {/* Natural Language Input Section */}
            <div className="space-y-4">
                <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
                    <NLRegistrationPanel
                        termId={selectedTerm}
                        onPlansGenerated={setPlans}
                        context={{ curriculum_strategy: curriculum }}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Sidebar Preferences */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm space-y-8">
                        <div className="flex items-center gap-3 text-blue-600 mb-2">
                            <Filter size={20} />
                            <h3 className="font-bold text-lg text-slate-800">Cấu hình sở thích</h3>
                        </div>

                        <div className="space-y-4">
                            <label className="text-sm font-bold text-slate-700">Tín chỉ mong muốn ({preferences.min_credits} - {preferences.max_credits})</label>
                            <div className="flex items-center gap-4">
                                <input
                                    type="range" min="10" max="25" step="1"
                                    value={preferences.max_credits}
                                    onChange={(e) => setPreferences({ ...preferences, max_credits: parseInt(e.target.value) })}
                                    className="flex-1 accent-blue-600"
                                />
                            </div>
                        </div>

                        <div className="space-y-4">
                            <label className="text-sm font-bold text-slate-700">Ngày muốn tránh</label>
                            <div className="grid grid-cols-2 gap-2">
                                {["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"].map(day => (
                                    <button
                                        key={day}
                                        onClick={() => {
                                            const newDays = preferences.avoid_days.includes(day)
                                                ? preferences.avoid_days.filter(d => d !== day)
                                                : [...preferences.avoid_days, day];
                                            setPreferences({ ...preferences, avoid_days: newDays });
                                        }}
                                        className={cn(
                                            "px-3 py-2 rounded-xl text-xs font-bold border transition-all",
                                            preferences.avoid_days.includes(day)
                                                ? "bg-red-50 border-red-100 text-red-600"
                                                : "bg-slate-50 border-slate-100 text-slate-500 hover:border-slate-200"
                                        )}
                                    >
                                        {day}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-3">
                            {[
                                { label: "Ưu tiên học sáng", key: "prefer_morning", icon: Sparkles },
                                { label: "Dồn lịch (Gọn ngày)", key: "compact_days", icon: Coffee }
                            ].map(opt => (
                                <button
                                    key={opt.key}
                                    onClick={() => setPreferences({ ...preferences, [opt.key]: !(preferences as any)[opt.key] })}
                                    className={cn(
                                        "w-full flex items-center justify-between px-4 py-3 rounded-2xl border transition-all",
                                        (preferences as any)[opt.key]
                                            ? "bg-indigo-50 border-indigo-100 text-indigo-700"
                                            : "bg-white border-slate-100 text-slate-500 hover:border-slate-200"
                                    )}
                                >
                                    <div className="flex items-center gap-3">
                                        <opt.icon size={18} />
                                        <span className="font-bold text-sm">{opt.label}</span>
                                    </div>
                                    <div className={cn(
                                        "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all",
                                        (preferences as any)[opt.key] ? "bg-indigo-600 border-indigo-600" : "border-slate-200"
                                    )}>
                                        {(preferences as any)[opt.key] && <div className="w-2 h-2 bg-white rounded-full" />}
                                    </div>
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={handleGenerate}
                            disabled={isGenerating}
                            className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl font-bold flex items-center justify-center gap-2 shadow-xl shadow-blue-100 transition-all active:scale-[0.98] disabled:opacity-50"
                        >
                            {isGenerating ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Sparkles size={20} />
                                    <span>Generate Plans</span>
                                </>
                            )}
                        </button>

                        {error && (
                            <div className="mt-3 p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-medium flex items-center gap-2">
                                <AlertCircle size={16} />
                                {error}
                            </div>
                        )}
                    </div>
                </div>

                {/* Results Area */}
                <div className="lg:col-span-8 space-y-6">
                    {plans.length === 0 && !isGenerating && !error && (
                        <div className="h-full min-h-[500px] flex flex-col items-center justify-center bg-white rounded-3xl border border-dashed border-slate-200 text-center p-12">
                            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 mb-6">
                                <Calendar size={40} />
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 mb-2">Chưa có kế hoạch nào</h3>
                            <p className="text-slate-500 max-w-sm font-medium">Hãy chọn sở thích và nhấn nút "Generate Plans" để xem các phương án lịch học tối ưu.</p>
                        </div>
                    )}

                    {plans.map((plan, idx) => (
                        <div
                            key={idx}
                            onClick={() => setPreviewingPlan(plan)}
                            className="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden hover:shadow-xl hover:border-blue-200 transition-all group cursor-pointer active:scale-[0.99]"
                        >
                            <div className="p-6 sm:p-8 flex flex-col sm:flex-row gap-6">
                                <div className="flex-1 space-y-4">
                                    <div className="flex items-center gap-3">
                                        <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm group-hover:scale-110 transition-transform">#{idx + 1}</span>
                                        <h4 className="text-xl font-bold text-slate-900">Optimization Plan</h4>
                                        <span className="px-3 py-1 bg-green-50 text-green-600 text-[10px] font-black uppercase tracking-widest rounded-full border border-green-100">Conflict-free</span>
                                    </div>

                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase tracking-widest font-black text-slate-400">Total Credits</p>
                                            <p className="font-bold text-slate-700 flex items-center gap-2">
                                                <CheckCircle2 size={16} className="text-blue-500" />
                                                {plan.total_credits}
                                            </p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase tracking-widest font-black text-slate-400">Days/Week</p>
                                            <p className="font-bold text-slate-700 flex items-center gap-2">
                                                <Calendar size={16} className="text-indigo-500" />
                                                {plan.score_breakdown.days_on_campus}
                                            </p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase tracking-widest font-black text-slate-400">Total Gaps</p>
                                            <p className="font-bold text-slate-700 flex items-center gap-2">
                                                <Clock size={16} className="text-orange-500" />
                                                {plan.score_breakdown.gaps_total_minutes}m
                                            </p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase tracking-widest font-black text-slate-400">Late Classes</p>
                                            <p className="font-bold text-slate-700 flex items-center gap-2">
                                                <AlertCircle size={16} className="text-red-400" />
                                                {plan.score_breakdown.evening_count}
                                            </p>
                                        </div>
                                    </div>

                                    <p className="text-sm text-slate-500 italic bg-slate-50 p-3 rounded-xl border border-slate-100 group-hover:bg-blue-50/50 group-hover:border-blue-100 transition-colors">"{plan.explanation}"</p>
                                </div>

                                <div className="sm:w-40 flex flex-col items-center justify-center border-t sm:border-t-0 sm:border-l border-slate-100 pt-6 sm:pt-0 sm:pl-6 gap-3">
                                    <div className="relative w-20 h-20">
                                        <svg className="w-full h-full transform -rotate-90">
                                            <circle cx="40" cy="40" r="34" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-100" />
                                            <circle cx="40" cy="40" r="34" stroke="currentColor" strokeWidth="8" fill="transparent"
                                                strokeDasharray={213}
                                                strokeDashoffset={213 - (213 * plan.quality_score) / 100}
                                                className="text-blue-600 transition-all duration-1000 group-hover:text-indigo-600"
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <span className="text-xl font-black text-slate-900">{Math.round(plan.quality_score)}</span>
                                            <span className="text-[8px] font-bold text-slate-400 uppercase">Điểm</span>
                                        </div>
                                    </div>
                                    <div className="w-full py-2.5 bg-blue-600 text-white rounded-xl text-xs font-black shadow-lg shadow-blue-100 group-hover:bg-indigo-600 group-hover:shadow-indigo-100 transition-all flex items-center justify-center gap-2">
                                        Xem chi tiết
                                        <ChevronRight size={14} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Plan Preview Modal */}
            {previewingPlan && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setPreviewingPlan(null)}>
                    <div className="bg-white rounded-[2rem] p-8 max-w-2xl w-full shadow-2xl space-y-8 animate-in fade-in zoom-in duration-200" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
                                    <Calendar size={28} />
                                </div>
                                <h3 className="text-2xl font-black text-slate-900">Chi tiết lộ trình học</h3>
                            </div>
                            <button onClick={() => setPreviewingPlan(null)} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-400">
                                <AlertCircle className="rotate-45" size={24} />
                            </button>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100">
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Tổng tín chỉ</p>
                                <p className="text-2xl font-black text-slate-900">{previewingPlan.total_credits} tín</p>
                            </div>
                            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100">
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Mức độ tối ưu</p>
                                <div className="flex items-center gap-2">
                                    <p className="text-2xl font-black text-blue-600">{Math.round(previewingPlan.quality_score)}%</p>
                                    <div className="h-1.5 flex-1 bg-slate-200 rounded-full overflow-hidden">
                                        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${previewingPlan.quality_score}%` }} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <p className="text-sm font-black text-slate-700 ml-1 uppercase tracking-widest">Danh sách học tập</p>
                            <div className="max-h-[350px] overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                                {previewingPlan.offerings?.map((off: any, idx: number) => (
                                    <div key={idx} className="group p-4 bg-white rounded-2xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/30 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4">
                                        <div className="flex items-start gap-4">
                                            <div className="flex-shrink-0 w-12 h-12 bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center rounded-xl transition-colors">
                                                <CheckCircle2 className="text-slate-400 group-hover:text-blue-600" size={20} />
                                            </div>
                                            <div>
                                                <p className="font-black text-slate-900 leading-tight">{off.course_code} - {off.course_name}</p>
                                                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                                                    <span className="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md uppercase">{off.class_code}</span>
                                                    <span className="text-[11px] font-bold text-blue-600 italic underline underline-offset-2">{off.credits} tín chỉ</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end text-right flex-shrink-0">
                                            <div className="flex items-center gap-2 text-indigo-700 font-bold text-xs bg-indigo-50 px-3 py-1.5 rounded-full border border-indigo-100">
                                                <Clock size={14} />
                                                <span>{off.day} · Tiết {off.start_period}-{off.end_period}</span>
                                            </div>
                                            <span className="text-[10px] font-bold text-slate-400 mt-2 uppercase">📍 Phòng {off.room}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="flex gap-4 pt-2">
                            <button
                                onClick={() => setPreviewingPlan(null)}
                                className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-black hover:bg-slate-200 transition-all"
                            >
                                Đóng
                            </button>
                            <button
                                onClick={() => {
                                    handleApplyPlan(previewingPlan);
                                    setPreviewingPlan(null);
                                }}
                                className="flex-[2] py-4 bg-blue-600 text-white rounded-2xl font-black shadow-xl shadow-blue-200 hover:bg-blue-700 transition-all transform active:scale-[0.98]"
                            >
                                Đăng ký ngay lộ trình này
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Registration Result Modal */}
            {registrationResult && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setRegistrationResult(null)}>
                    <div className="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl space-y-6" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-3">
                            {registrationResult.status === "success" ? (
                                <CheckCircle2 size={28} className="text-green-500" />
                            ) : (
                                <AlertCircle size={28} className="text-red-500" />
                            )}
                            <h3 className="text-xl font-bold text-slate-900">
                                {registrationResult.status === "success" ? "Đăng ký thành công!" : "Lỗi đăng ký"}
                            </h3>
                        </div>
                        <p className="text-slate-600 font-medium">{registrationResult.message}</p>
                        {registrationResult.registered_courses && registrationResult.registered_courses.length > 0 && (
                            <div className="space-y-2">
                                <p className="text-sm font-bold text-slate-700">Các môn đã đăng ký:</p>
                                <div className="max-h-60 overflow-y-auto space-y-2">
                                    {registrationResult.registered_courses.map((c: any, i: number) => (
                                        <div key={i} className="flex items-center justify-between bg-green-50 p-3 rounded-xl border border-green-100">
                                            <div>
                                                <p className="font-bold text-sm text-slate-800">{c.course_code} - {c.name}</p>
                                                <p className="text-xs text-slate-500">{c.class_code} · {c.day} · {c.period} · {c.room}</p>
                                            </div>
                                            <CheckCircle2 size={16} className="text-green-500 flex-shrink-0" />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        <button
                            onClick={() => setRegistrationResult(null)}
                            className="w-full py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-colors"
                        >
                            Đóng
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PlannerPage;
