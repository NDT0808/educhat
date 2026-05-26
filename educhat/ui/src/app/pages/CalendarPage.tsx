import React, { useState, useEffect } from "react";
import {
    Download,
    Calendar as CalendarIcon,
    Clock,
    Info,
    CheckCircle2,
    ExternalLink,
    ChevronRight
} from "lucide-react";
import { apiService } from "../services/apiService";
import { useAuth } from "../context/AuthContext";
import { cn } from "../utils/cn";

const CalendarPage: React.FC = () => {
    const { user } = useAuth();
    const [terms, setTerms] = useState<any[]>([]);
    const [selectedTerm, setSelectedTerm] = useState("");

    useEffect(() => {
        apiService.getTerms().then(res => {
            setTerms(res.terms);
            if (res.terms.length > 0) setSelectedTerm(res.terms[0].id);
        });
    }, []);

    const handleExportICS = () => {
        const url = apiService.getCalendarIcsUrl(Number(user?.id) || 1, selectedTerm);
        window.open(url, "_blank");
    };

    const currentTermData = terms.find(t => t.id === selectedTerm);

    const milestones = [
        { name: "Mở đăng ký", date: currentTermData?.reg_start, type: "registration" },
        { name: "Đóng đăng ký", date: currentTermData?.reg_end, type: "registration" },
        { name: "Bắt đầu học kỳ", date: currentTermData?.start_date, type: "term" },
        { name: "Kết thúc học kỳ", date: currentTermData?.end_date, type: "term" },
    ];

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Academic Calendar</h1>
                    <p className="text-slate-500 font-medium">Theo dõi các mốc quan trọng và đồng bộ lịch học với cá nhân.</p>
                </div>

                <div className="flex items-center gap-3">
                    <select
                        value={selectedTerm}
                        onChange={(e) => setSelectedTerm(e.target.value)}
                        className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                    >
                        {terms.map(term => (
                            <option key={term.id} value={term.id}>{term.name}</option>
                        ))}
                    </select>

                    <button
                        onClick={handleExportICS}
                        className="bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 hover:bg-blue-700 transition-all shadow-lg shadow-blue-100"
                    >
                        <Download size={18} />
                        Export ICS
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Timeline Card */}
                <div className="lg:col-span-2 bg-white rounded-3xl p-8 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                            <CalendarIcon size={20} />
                        </div>
                        <h2 className="text-xl font-bold text-slate-800">Term Timeline</h2>
                    </div>

                    <div className="relative pl-8 space-y-8 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
                        {milestones.map((m, i) => (
                            <div key={i} className="relative">
                                <div className={cn(
                                    "absolute -left-[30px] w-5 h-5 rounded-full border-4 border-white shadow-sm z-10",
                                    m.type === "registration" ? "bg-orange-500" : "bg-blue-600"
                                )} />
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-5 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-colors group">
                                    <div>
                                        <p className="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors">{m.name}</p>
                                        <p className="text-xs font-medium text-slate-500">{m.type === "registration" ? "Cổng đăng ký tín chỉ" : "Thời gian đào tạo"}</p>
                                    </div>
                                    <div className="flex items-center gap-2 px-3 py-1 bg-white rounded-lg border border-slate-100 shadow-sm text-xs font-black text-slate-600">
                                        <Clock size={14} className="text-slate-400" />
                                        {m.date || "TBD"}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Info Card */}
                <div className="space-y-6">
                    <div className="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-3xl p-8 text-white shadow-xl shadow-blue-200 relative overflow-hidden">
                        <div className="absolute top-[-10%] right-[-10%] w-32 h-32 bg-white/10 rounded-full blur-2xl" />
                        <div className="relative z-10 space-y-4">
                            <Info size={32} className="text-blue-200" />
                            <h3 className="text-xl font-bold">Sync to Calendar</h3>
                            <p className="text-indigo-100 text-sm font-medium leading-relaxed">
                                Xuất lịch học chính thức sang Apple Calendar, Google Calendar hoặc Outlook để không bỏ lỡ tiết học nào.
                            </p>
                            <button className="flex items-center gap-2 text-sm font-black text-white hover:text-blue-200 transition-colors group">
                                Learn how it works
                                <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
                            </button>
                        </div>
                    </div>

                    <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm space-y-6">
                        <h4 className="font-bold text-slate-800 flex items-center gap-2">
                            <CheckCircle2 size={18} className="text-green-500" />
                            Checklist
                        </h4>
                        <ul className="space-y-4">
                            {[
                                "Kiểm tra kỹ mã lớp trước khi đăng ký",
                                "Đóng học phí trước deadline",
                                "Cập nhật email phản hồi của giảng viên"
                            ].map((item, idx) => (
                                <li key={idx} className="flex gap-3 text-sm font-medium text-slate-600">
                                    <div className="w-1.5 h-1.5 rounded-full bg-slate-300 mt-2 flex-shrink-0" />
                                    {item}
                                </li>
                            ))}
                        </ul>
                        <button className="w-full py-3 rounded-xl border-2 border-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-50 transition-colors flex items-center justify-center gap-2">
                            View Handbook
                            <ExternalLink size={14} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CalendarPage;
