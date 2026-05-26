import { useState, useEffect, useRef } from "react";
import { apiService } from "../services/apiService";
import { X, Calendar, AlertCircle, Search, ChevronLeft } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface ScheduleOptimizerModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialCourses?: string[];
    initialConstraints?: string[];
}

interface Course {
    course_code: string;
    name: string;
}

export default function ScheduleOptimizerModal({
    isOpen,
    onClose,
    initialCourses = [],
    initialConstraints = []
}: ScheduleOptimizerModalProps) {
    // UI State
    const [step, setStep] = useState<"input" | "result">("input");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // Data State
    const [availableCourses, setAvailableCourses] = useState<Course[]>([]);
    const [selectedCourses, setSelectedCourses] = useState<Course[]>([]);

    // Search State
    const [searchQuery, setSearchQuery] = useState("");
    const [showDropdown, setShowDropdown] = useState(false);
    const searchRef = useRef<HTMLDivElement>(null);

    // Schedule Results
    const [schedules, setSchedules] = useState<any[]>([]);
    const [applyingId, setApplyingId] = useState<number | null>(null);
    const { user } = useAuth();

    // Load available courses on mount/open
    useEffect(() => {
        if (isOpen) {
            loadCourses();
            // Reset to input step
            setStep("input");
            setSchedules([]);
            setError("");
        }
    }, [isOpen]);

    // Handle clicking outside search dropdown
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const loadCourses = async () => {
        try {
            const res = await apiService.getCourses();
            if (res.status === "success") {
                setAvailableCourses(res.courses);

                // Map initial codes to full objects if possible
                if (initialCourses.length > 0) {
                    const initSelected = res.courses.filter((c: Course) =>
                        initialCourses.includes(c.course_code)
                    );
                    setSelectedCourses(initSelected);
                    // If initial courses provided (e.g. from chat), auto-optimize?
                    // User said "sau khi bấm optimize", so maybe manual is preferred.
                } else {
                    setSelectedCourses([]);
                }
            }
        } catch (err) {
            console.error("Failed to load courses", err);
        }
    };

    const handleSelectCourse = (course: Course) => {
        if (!selectedCourses.find(c => c.course_code === course.course_code)) {
            setSelectedCourses([...selectedCourses, course]);
        }
        setSearchQuery("");
        setShowDropdown(false);
    };

    const handleRemoveCourse = (code: string) => {
        setSelectedCourses(selectedCourses.filter(c => c.course_code !== code));
    };

    const handleOptimize = async () => {
        if (selectedCourses.length === 0) {
            setError("Please select at least one course.");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const courseCodes = selectedCourses.map(c => c.course_code);
            // Use initialConstraints passed from Chat (if any), or empty since we removed UI checkboxes
            const data = await apiService.optimizeSchedule(courseCodes, initialConstraints);

            if (data.status === "success" && data.schedules) {
                setSchedules(data.schedules);
                if (data.schedules.length === 0) {
                    setError("No valid schedules found. Try fewer courses.");
                } else {
                    setStep("result"); // Switch to result view
                }
            } else {
                setError("Failed to generate schedules.");
            }
        } catch (err) {
            setError("Could not connect to optimizer service.");
        } finally {
            setLoading(false);
        }
    };

    const handleApplySchedule = async (schedule: any[], index: number) => {
        if (!user || !user.id || user.role === "ADMIN") {
            alert("Bạn cần đăng nhập bằng tài khoản sinh viên để lưu lịch học.");
            return;
        }

        setApplyingId(index);
        try {
            // Extract offering IDs from the schedule
            const offeringIds = schedule.map(item => item.id);
            await apiService.applyPlan(parseInt(user.id), "2024.1", offeringIds);
            alert("Lưu lịch học thành công! Bạn có thể xem lịch trong mục Thời khóa biểu.");
            onClose();
            // Dispatch event to refresh timetable if needed
            window.dispatchEvent(new Event("refreshTimetable"));
        } catch (err) {
            console.error("Failed to apply plan:", err);
            alert("Đã xảy ra lỗi khi lưu lịch học. Vui lòng thử lại.");
        } finally {
            setApplyingId(null);
        }
    };

    const filteredCourses = availableCourses.filter(c =>
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.course_code.toLowerCase().includes(searchQuery.toLowerCase())
    ).slice(0, 10); // Limit to 10 suggestions

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-100 bg-white z-10">
                    <div className="flex items-center gap-3">
                        {step === "result" && (
                            <button
                                onClick={() => setStep("input")}
                                className="mr-2 p-1.5 hover:bg-slate-100 rounded-full text-slate-500 transition-colors"
                            >
                                <ChevronLeft size={24} />
                            </button>
                        )}
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <Calendar size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-slate-800">
                                {step === "input" ? "Course Selection" : "Optimization Results"}
                            </h2>
                            <p className="text-sm text-slate-500">
                                {step === "input" ? "Select courses to build your schedule" : `Found ${schedules.length} valid schedule options`}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-auto p-6 bg-slate-50/50">

                    {error && (
                        <div className="mb-6 p-4 bg-red-50 text-red-600 text-sm rounded-xl flex items-start gap-2 border border-red-100 animate-in fade-in slide-in-from-top-2">
                            <AlertCircle size={16} className="mt-0.5 shrink-0" />
                            {error}
                        </div>
                    )}

                    {/* Step 1: Input */}
                    {step === "input" && (
                        <div className="max-w-2xl mx-auto space-y-8">
                            {/* Search Bar */}
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-slate-700">Add Courses</label>
                                <div className="relative" ref={searchRef}>
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                                        <input
                                            type="text"
                                            value={searchQuery}
                                            onChange={(e) => {
                                                setSearchQuery(e.target.value);
                                                setShowDropdown(true);
                                            }}
                                            onFocus={() => setShowDropdown(true)}
                                            placeholder="Search by name or code (e.g. 'Nội khoa', 'YD101')..."
                                            className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm text-slate-700 placeholder:text-slate-400"
                                        />
                                    </div>

                                    {/* Dropdown Suggestions */}
                                    {showDropdown && searchQuery && (
                                        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden z-20 max-h-60 overflow-y-auto">
                                            {filteredCourses.length > 0 ? (
                                                filteredCourses.map(course => (
                                                    <button
                                                        key={course.course_code}
                                                        onClick={() => handleSelectCourse(course)}
                                                        className="w-full text-left px-4 py-3 hover:bg-indigo-50 flex items-center justify-between group transition-colors"
                                                    >
                                                        <span className="font-medium text-slate-700 group-hover:text-indigo-700">
                                                            {course.name}
                                                        </span>
                                                        <span className="text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded group-hover:bg-indigo-100 group-hover:text-indigo-600">
                                                            {course.course_code}
                                                        </span>
                                                    </button>
                                                ))
                                            ) : (
                                                <div className="px-4 py-3 text-slate-400 text-sm text-center">
                                                    No courses found.
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Selected Chips */}
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <label className="block text-sm font-medium text-slate-700">
                                        Selected Courses ({selectedCourses.length})
                                    </label>
                                    {selectedCourses.length > 0 && (
                                        <button
                                            onClick={() => setSelectedCourses([])}
                                            className="text-xs text-red-500 hover:text-red-600 font-medium"
                                        >
                                            Clear All
                                        </button>
                                    )}
                                </div>
                                <div className="min-h-[100px] p-4 bg-white border border-slate-200 rounded-xl flex flex-wrap content-start gap-2">
                                    {selectedCourses.length > 0 ? (
                                        selectedCourses.map(course => (
                                            <div
                                                key={course.course_code}
                                                className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 border border-indigo-100 rounded-full text-sm text-indigo-700 group hover:border-indigo-200 transition-colors"
                                            >
                                                <span>{course.name}</span>
                                                <button
                                                    onClick={() => handleRemoveCourse(course.course_code)}
                                                    className="p-0.5 hover:bg-white rounded-full text-indigo-400 hover:text-red-500 transition-colors"
                                                >
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-slate-300 text-sm italic">
                                            No courses selected yet.
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Optimize Button */}
                            <div className="pt-4">
                                <button
                                    onClick={handleOptimize}
                                    disabled={loading || selectedCourses.length === 0}
                                    className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-indigo-200 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
                                >
                                    {loading ? (
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    ) : (
                                        <Calendar size={20} />
                                    )}
                                    {loading ? "Generatng Schedules..." : "Find Best Schedules"}
                                </button>
                                <p className="text-center text-xs text-slate-400 mt-3">
                                    * Schedules are optimized based on time and room availability.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Results */}
                    {step === "result" && (
                        <div className="space-y-6">
                            <div className="grid gap-6">
                                {schedules.map((sched, idx) => (
                                    <div
                                        key={idx}
                                        className="bg-white border boundary border-slate-200 rounded-xl overflow-hidden hover:shadow-lg transition-all duration-300 group"
                                    >
                                        <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center font-bold text-indigo-600 shadow-sm">
                                                    {idx + 1}
                                                </div>
                                                <span className="font-semibold text-slate-700">Option {idx + 1}</span>
                                            </div>
                                            <button
                                                className="text-sm font-medium px-4 py-2 bg-indigo-600 text-white rounded-lg shadow-sm hover:bg-indigo-700 active:scale-95 transition-all disabled:opacity-50"
                                                onClick={() => handleApplySchedule(sched, idx)}
                                                disabled={applyingId === idx}
                                            >
                                                {applyingId === idx ? "Đang lưu..." : "Chọn lịch này"}
                                            </button>
                                        </div>

                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="bg-white border-b border-slate-100">
                                                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Class Code</th>
                                                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Course Name</th>
                                                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Time</th>
                                                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Day</th>
                                                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Room</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-slate-50">
                                                    {sched.map((item: any, i: number) => (
                                                        <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                                                            <td className="px-6 py-4 text-slate-600 font-mono text-xs font-medium">
                                                                {item.class_code || item.course_code}
                                                            </td>
                                                            <td className="px-6 py-4 text-slate-800 font-medium">
                                                                {item.name}
                                                            </td>
                                                            <td className="px-6 py-4 text-slate-600">
                                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                                                                    Block {Math.ceil(item.start_period / 3)} ({item.start_period}-{item.end_period})
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${item.day_of_week === 'Thứ 7' || item.day_of_week === 'Chủ nhật'
                                                                    ? 'bg-orange-50 text-orange-700 border-orange-200'
                                                                    : 'bg-indigo-50 text-indigo-700 border-indigo-200'
                                                                    }`}>
                                                                    {item.day_of_week}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4 text-slate-500 text-xs font-mono">
                                                                {item.room}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
