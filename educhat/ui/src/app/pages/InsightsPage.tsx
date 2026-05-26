import React, { useState, useEffect } from "react";
import {
    BarChart3,
    TrendingUp,
    Users,
    ShieldCheck,
    Search,
    ArrowUpRight,
    CheckCircle2
} from "lucide-react";
import { apiService } from "../services/apiService";
import { cn } from "../utils/cn";

const InsightsPage: React.FC = () => {
    const [terms, setTerms] = useState<any[]>([]);
    const [selectedTerm, setSelectedTerm] = useState("");
    const [courses, setCourses] = useState<any[]>([]);
    const [selectedCourse, setSelectedCourse] = useState<number | undefined>(undefined);
    const [heatmap, setHeatmap] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        apiService.getTerms().then(res => {
            setTerms(res.terms);
            if (res.terms.length > 0) setSelectedTerm(res.terms[0].id);
        });
        apiService.getCourses().then(res => setCourses(res.courses));
    }, []);

    useEffect(() => {
        if (selectedTerm) {
            setIsLoading(true);
            apiService.getFeedbackHeatmap(selectedTerm, selectedCourse)
                .then(res => setHeatmap(res))
                .finally(() => setIsLoading(false));
        }
    }, [selectedTerm, selectedCourse]);

    const metrics = [
        { label: "Workload", key: "workload", color: "bg-orange-500" },
        { label: "Materials", key: "materials", color: "bg-blue-500" },
        { label: "Practical", key: "practical", color: "bg-green-500" },
        { label: "Fairness", key: "fairness", color: "bg-purple-500" },
        { label: "Support", key: "support", color: "bg-indigo-500" },
        { label: "Overall", key: "overall", color: "bg-red-500" }
    ];

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Student Insights</h1>
                    <p className="text-slate-500 font-medium">Khám phá chất lượng môn học thông qua dữ liệu cộng đồng.</p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <select
                        value={selectedTerm}
                        onChange={(e) => setSelectedTerm(e.target.value)}
                        className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-bold text-slate-700 outline-none"
                    >
                        {terms.map(term => <option key={term.id} value={term.id}>{term.name}</option>)}
                    </select>

                    <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <select
                            value={selectedCourse || ""}
                            onChange={(e) => setSelectedCourse(e.target.value ? parseInt(e.target.value) : undefined)}
                            className="bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm font-bold text-slate-700 outline-none min-w-[200px]"
                        >
                            <option value="">Tất cả môn học</option>
                            {courses.map(course => <option key={course.course_code} value={1}>{course.name}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Main Heatmap */}
                <div className="lg:col-span-8 space-y-8">
                    <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm relative overflow-hidden">
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center">
                                    <BarChart3 size={20} />
                                </div>
                                <h2 className="text-xl font-bold text-slate-800">Quality Heatmap</h2>
                            </div>
                            {heatmap?.sample_size >= 5 && (
                                <div className="flex items-center gap-2 px-3 py-1 bg-green-50 text-green-600 rounded-full text-xs font-bold border border-green-100">
                                    <ShieldCheck size={14} />
                                    Dữ liệu ẩn danh
                                </div>
                            )}
                        </div>

                        {isLoading ? (
                            <div className="h-[400px] flex items-center justify-center">
                                <div className="w-10 h-10 border-4 border-slate-100 border-t-blue-600 rounded-full animate-spin" />
                            </div>
                        ) : heatmap?.sample_size < 5 ? (
                            <div className="h-[400px] flex flex-col items-center justify-center text-center space-y-4 px-12">
                                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center text-slate-300">
                                    <Users size={32} />
                                </div>
                                <h3 className="text-lg font-bold text-slate-800">Chưa đủ dữ liệu</h3>
                                <p className="text-sm text-slate-500 font-medium">Cần tối thiểu 5 phản hồi để hiển thị biểu đồ nhiệt nhằm bảo vệ tính ẩn danh của sinh viên.</p>
                                <p className="text-xs font-bold text-blue-600">Hiện có: {heatmap?.sample_size || 0} phản hồi</p>
                            </div>
                        ) : (
                            <div className="space-y-8">
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
                                    {metrics.map(m => (
                                        <div key={m.key} className="space-y-3">
                                            <div className="flex justify-between items-end">
                                                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">{m.label}</p>
                                                <p className="text-lg font-black text-slate-900">{heatmap?.avg_scores?.[m.key]?.toFixed(1) || "0.0"}</p>
                                            </div>
                                            <div className="h-2 bg-slate-50 rounded-full overflow-hidden">
                                                <div
                                                    className={cn("h-full rounded-full transition-all duration-1000", m.color)}
                                                    style={{ width: `${((heatmap?.avg_scores?.[m.key] || 0) / 5) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {heatmap?.tag_counts && Object.keys(heatmap.tag_counts).length > 0 && (
                                    <div className="pt-8 border-t border-slate-50">
                                        <p className="text-sm font-bold text-slate-700 mb-4">Top Tags</p>
                                        <div className="flex flex-wrap gap-2">
                                            {Object.entries(heatmap.tag_counts).map(([tag, count]: any) => (
                                                <div key={tag} className="px-4 py-2 bg-slate-50 border border-slate-100 rounded-2xl flex items-center gap-3">
                                                    <span className="text-sm font-bold text-slate-700">{tag}</span>
                                                    <span className="px-2 py-0.5 bg-white rounded-lg text-[10px] font-black text-blue-600 border border-slate-100">{count}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar Insights */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 text-white space-y-6">
                        <div className="flex items-center gap-3 text-emerald-400">
                            <TrendingUp size={24} />
                            <h3 className="text-lg font-bold">Quick Facts</h3>
                        </div>

                        <div className="space-y-6">
                            <div className="flex items-center justify-between group cursor-pointer">
                                <div>
                                    <p className="text-xs font-bold text-slate-400">Trend môn học</p>
                                    <p className="text-sm font-bold group-hover:text-emerald-400 transition-colors">Lập trình hướng đối tượng</p>
                                </div>
                                <ArrowUpRight size={18} className="text-slate-600 group-hover:text-white transition-colors" />
                            </div>
                            <div className="flex items-center justify-between group cursor-pointer">
                                <div>
                                    <p className="text-xs font-bold text-slate-400">Giảng viên nổi bật</p>
                                    <p className="text-sm font-bold group-hover:text-emerald-400 transition-colors">Bộ môn Công nghệ phần mềm</p>
                                </div>
                                <ArrowUpRight size={18} className="text-slate-600 group-hover:text-white transition-colors" />
                            </div>
                        </div>

                        <div className="pt-6 border-t border-slate-800 flex items-center justify-between">
                            <div>
                                <p className="text-2xl font-black">{heatmap?.sample_size || 0}</p>
                                <p className="text-[10px] uppercase font-black text-slate-500 tracking-widest">Total Reviews</p>
                            </div>
                            <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400">
                                <BarChart3 size={20} />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm">
                        <h4 className="font-bold text-slate-800 mb-4">Ghi chú cộng đồng</h4>
                        <div className="space-y-4">
                            <p className="text-sm text-slate-500 font-medium italic">
                                "Dữ liệu được tổng hợp từ sinh viên các khóa trước. Vui lòng tham khảo có chọn lọc."
                            </p>
                            <div className="flex items-center gap-2 text-blue-600 text-xs font-bold">
                                <CheckCircle2 size={14} />
                                Xác thực bởi EduChat
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InsightsPage;
