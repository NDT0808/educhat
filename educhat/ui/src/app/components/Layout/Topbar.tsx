import React from "react";
import { User, Bell } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const Topbar: React.FC = () => {
    const { user } = useAuth();
    const path = window.location.pathname;
    const titleMap: Record<string, string> = {
        "/": "Tư vấn học tập",
        "/planner": "Planner",
        "/calendar": "Calendar",
        "/feedback": "Feedback",
        "/insights": "Insights",
        "/curriculum": "Lộ trình học tập",
        "/timetable": "Thời khóa biểu",
        "/knowledge": "Knowledge",
        "/settings": "Settings",
        "/admin": "Admin Console",
    };

    return (
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between gap-3 px-4 sm:px-6 lg:px-8 sticky top-0 z-20">
            <div className="flex min-w-0 items-center gap-4">
                <h2 className="truncate text-base font-semibold text-slate-900">
                    {titleMap[path] || path.substring(1).replace("/", " / ")}
                </h2>
            </div>

            <div className="flex shrink-0 items-center gap-2 sm:gap-4">
                <button className="p-2 rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors relative" aria-label="Notifications">
                    <Bell size={20} />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
                </button>

                <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-semibold text-slate-900 leading-tight">{user?.name}</p>
                        <p className="text-xs font-medium text-slate-500 capitalize">{user?.role.toLowerCase()}</p>
                    </div>
                    <div className="w-9 h-9 rounded-md bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
                        <User size={20} />
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Topbar;
