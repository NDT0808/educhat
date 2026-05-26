import { useState, useEffect } from "react";
import { apiService } from "../services/apiService";
import { Calendar, Search, Check, ChevronRight } from "lucide-react";

interface CourseSelectionBubbleProps {
    initialConstraints: string[];
    onOptimize: (courses: string[], constraints: string[]) => void;
}

export default function CourseSelectionBubble({
    initialConstraints,
    onOptimize,
}: CourseSelectionBubbleProps) {
    const [courses, setCourses] = useState<any[]>([]);
    const [selectedCourses, setSelectedCourses] = useState<string[]>([]);
    const [constraints, setConstraints] = useState<string[]>(initialConstraints);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [resultCount, setResultCount] = useState<number | null>(null);

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                const data = await apiService.getAvailableCourses();
                if (data.status === "success") {
                    setCourses(data.courses);
                }
            } catch (error) {
                console.error("Failed to load courses", error);
            } finally {
                setLoading(false);
            }
        };
        fetchCourses();
    }, []);

    const toggleCourse = (code: string) => {
        if (selectedCourses.includes(code)) {
            setSelectedCourses(selectedCourses.filter((c) => c !== code));
        } else {
            setSelectedCourses([...selectedCourses, code]);
        }
    };

    const removeConstraint = (c: string) => {
        setConstraints(constraints.filter((item) => item !== c));
    };

    const handleOptimizeClick = async () => {
        if (selectedCourses.length === 0) return;
        setIsOptimizing(true);
        // Call the parent optimization handler (which will likely display results or open the modal with results)
        // For now, we assume the parent handles showing the results.
        // Actually, to make it "in-chat", maybe we fetch here and show short result?
        // Let's stick passing it up or doing it here.
        try {
            // We will pass the data up to the container to handle result display
            // OR we can display results inline here. Let's try inline for "chat bubble" feel.
            const data = await apiService.optimizeSchedule(selectedCourses, constraints);
            if (data.status === "success") {
                setResultCount(data.schedules.length);
                onOptimize(selectedCourses, constraints); // Allow parent to also know or open a full view if needed
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsOptimizing(false);
        }
    };

    const filteredCourses = courses.filter(
        (c) =>
            c.course_code.toLowerCase().includes(search.toLowerCase()) ||
            c.name.toLowerCase().includes(search.toLowerCase())
    );

    if (loading) return <div className="p-4 bg-slate-50 rounded-xl animate-pulse w-64 h-32"></div>;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden w-full max-w-md my-2">
            <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-4 border-b border-indigo-100">
                <h3 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
                    <Calendar size={16} />
                    Course Selection
                </h3>

                {/* Constraints Chips */}
                <div className="flex flex-wrap gap-2 mt-2">
                    {constraints.map((c) => (
                        <span key={c} className="text-xs px-2 py-1 bg-white border border-indigo-100 text-indigo-600 rounded-full flex items-center gap-1 shadow-sm">
                            {c}
                            <button onClick={() => removeConstraint(c)} className="hover:text-red-500">
                                &times;
                            </button>
                        </span>
                    ))}
                    {constraints.length === 0 && (
                        <span className="text-xs text-slate-400 italic">No constraints detected</span>
                    )}
                </div>
            </div>

            <div className="p-4">
                {/* Course Search */}
                <div className="relative mb-3">
                    <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                    <input
                        type="text"
                        placeholder="Search courses..."
                        className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                {/* Course List */}
                <div className="max-h-48 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                    {filteredCourses.map(course => (
                        <label key={course.course_code} className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${selectedCourses.includes(course.course_code) ? "bg-blue-50 border border-blue-100" : "hover:bg-slate-50 border border-transparent"}`}>
                            <div className={`w-4 h-4 rounded border flex items-center justify-center ${selectedCourses.includes(course.course_code) ? "bg-blue-600 border-blue-600" : "border-slate-300 bg-white"}`}>
                                {selectedCourses.includes(course.course_code) && <Check size={12} className="text-white" />}
                            </div>
                            <input type="checkbox" className="hidden" checked={selectedCourses.includes(course.course_code)} onChange={() => toggleCourse(course.course_code)} />
                            <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-slate-700 truncate">{course.name}</div>
                                <div className="text-xs text-slate-400">{course.course_code}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>

            <div className="p-4 border-t border-slate-50 bg-slate-50/50 flex justify-between items-center">
                <span className="text-xs font-medium text-slate-500">
                    {selectedCourses.length} selected
                </span>
                <button
                    onClick={handleOptimizeClick}
                    disabled={selectedCourses.length === 0 || isOptimizing}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {isOptimizing ? "Processing..." : (
                        <>
                            Optimize <ChevronRight size={16} />
                        </>
                    )}
                </button>
            </div>

            {resultCount !== null && (
                <div className="bg-green-50 p-3 text-center text-xs text-green-700 border-t border-green-100">
                    Found {resultCount} schedule options! Check the main results view.
                </div>
            )}
        </div>
    );
}
