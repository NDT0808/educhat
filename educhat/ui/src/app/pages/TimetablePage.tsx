import React, { useState, useEffect } from "react";
import { Calendar, Clock, MapPin, ChevronLeft, ChevronRight } from "lucide-react";
import { apiService } from "../services/apiService";
import { cn } from "../utils/cn";

const TimetablePage: React.FC = () => {
    const [terms, setTerms] = useState<any[]>([]);
    const [selectedTerm, setSelectedTerm] = useState("");
    const [timetable, setTimetable] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        apiService.getTerms().then(res => {
            setTerms(res.terms);
            if (res.terms.length > 0) setSelectedTerm(res.terms[0].id);
        });
    }, []);

    useEffect(() => {
        if (!selectedTerm) return;
        setLoading(true);
        apiService.getTimetable(selectedTerm)
            .then(res => {
                if (res.status === 'success') {
                    setTimetable(res.timetable);
                }
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [selectedTerm]);

    // Grid configuration
    const periods = Array.from({ length: 12 }, (_, i) => i + 1);
    const days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];

    const getCourseForCell = (day: string, period: number) => {
        return timetable.find(item =>
            item.day_of_week === day &&
            period >= item.start_period &&
            period <= item.end_period
        );
    };

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 mb-1">Thời khóa biểu</h1>
                    <p className="text-slate-500 font-medium">Lịch học chính quy học kỳ {terms.find(t => t.id === selectedTerm)?.name}</p>
                </div>

                <div className="flex items-center gap-2 bg-white p-1.5 rounded-xl border border-slate-200 shadow-sm">
                    <select
                        value={selectedTerm}
                        onChange={(e) => setSelectedTerm(e.target.value)}
                        className="bg-transparent text-sm font-bold text-slate-700 outline-none px-2 py-1"
                    >
                        {terms.map(t => (
                            <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="flex-1 bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                {/* Header Row */}
                <div className="grid grid-cols-8 border-b border-slate-200 bg-slate-50">
                    <div className="p-4 border-r border-slate-200 flex items-center justify-center font-bold text-slate-400 text-xs uppercase tracking-wider">
                        Tiết / Ngày
                    </div>
                    {days.map(day => (
                        <div key={day} className="p-4 border-r border-slate-200 last:border-r-0 flex items-center justify-center font-bold text-slate-700 text-sm">
                            {day}
                        </div>
                    ))}
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto">
                    {loading ? (
                        <div className="h-full flex items-center justify-center text-slate-400">Đang tải lịch học...</div>
                    ) : (
                        <div className="grid grid-cols-8 auto-rows-[minmax(60px,1fr)]">
                            {periods.map(period => (
                                <React.Fragment key={period}>
                                    {/* Period Label */}
                                    <div className="border-b border-r border-slate-100 p-2 flex flex-col items-center justify-center bg-slate-50/50 text-xs font-bold text-slate-400"
                                        style={{ gridColumn: 1, gridRow: period }}
                                    >
                                        <span>Tiết {period}</span>
                                    </div>

                                    {/* Empty Grid Cells for Borders */}
                                    {days.map((day, dIndex) => (
                                        <div
                                            key={`grid-${day}-${period}`}
                                            className="border-b border-r border-slate-100 p-2 min-h-[60px]"
                                            style={{ gridColumn: dIndex + 2, gridRow: period }}
                                        />
                                    ))}
                                </React.Fragment>
                            ))}

                            {/* Overlay Courses with Explicit Placement */}
                            {timetable.map((course, idx) => {
                                const dayIndex = days.indexOf(course.day_of_week);
                                if (dayIndex === -1) return null;

                                const colStart = dayIndex + 2; // Col 1 is labels
                                const rowStart = course.start_period;
                                const rowSpan = course.end_period - course.start_period + 1;

                                return (
                                    <div
                                        key={`course-${course.id || idx}`}
                                        className="p-1 relative z-10"
                                        style={{
                                            gridColumn: colStart,
                                            gridRow: `${rowStart} / span ${rowSpan}`
                                        }}
                                    >
                                        <div className="w-full h-full bg-blue-50 border border-blue-100 rounded-xl p-2 flex flex-col gap-1 hover:shadow-md transition-shadow cursor-pointer overflow-hidden group">
                                            <div className="flex justify-between items-start">
                                                <span className="text-[10px] font-black text-blue-400 uppercase tracking-wider">{course.class_code}</span>
                                                <span className="text-[10px] font-bold bg-white text-blue-600 px-1.5 rounded-md shadow-sm">{course.room}</span>
                                            </div>
                                            <p className="text-xs font-bold text-slate-700 line-clamp-2 leading-tight group-hover:text-blue-700">{course.name}</p>
                                            <div className="mt-auto flex items-center gap-1 text-[10px] text-blue-500 font-medium">
                                                <Clock size={10} />
                                                {course.start_period} - {course.end_period}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TimetablePage;
