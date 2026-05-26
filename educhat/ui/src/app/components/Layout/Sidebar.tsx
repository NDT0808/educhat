import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
    MessageSquare,
    Search,
    Settings,
    ShieldAlert,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Sparkles,
    Calendar,
    Star,
    BarChart3,
    CheckCircle2,
    ScanLine
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { cn } from "../../utils/cn";

interface SidebarProps {
    isCollapsed: boolean;
    setIsCollapsed: (collapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, setIsCollapsed }) => {
    const { user, logout } = useAuth();
    const location = useLocation();

    const menuItems = [
        { name: "Tư vấn", icon: MessageSquare, path: "/", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "Lộ trình", icon: Sparkles, path: "/curriculum", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "Thời khóa biểu", icon: Calendar, path: "/timetable", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "Planner", icon: CheckCircle2, path: "/planner", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "Feedback", icon: Star, path: "/feedback", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "OCR Scanner", icon: ScanLine, path: "/ocr", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "Insights", icon: BarChart3, path: "/insights", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "Knowledge", icon: Search, path: "/knowledge", roles: ["USER", "student", "STUDENT", "ADMIN"] },
        { name: "Admin Console", icon: ShieldAlert, path: "/admin", roles: ["ADMIN"] },
        { name: "Settings", icon: Settings, path: "/settings", roles: ["USER", "student", "STUDENT", "ADMIN"] },
    ];

    const filteredItems = menuItems.filter(item =>
        item.roles.includes(user?.role || "")
    );

    return (
        <aside
            className={cn(
                "relative flex flex-col bg-slate-950 text-white border-r border-slate-900 transition-all duration-300 ease-in-out z-30",
                isCollapsed ? "w-16 sm:w-20" : "w-64"
            )}
        >
            <div className={cn(
                "flex items-center justify-between h-20 border-b border-white/10",
                isCollapsed ? "p-3" : "p-5"
            )}>
                {!isCollapsed && (
                    <div>
                        <span className="text-lg font-semibold tracking-tight text-white">EduChat</span>
                        <p className="text-xs text-slate-400 mt-0.5">Academic assistant</p>
                    </div>
                )}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="p-1.5 rounded-md bg-white/5 hover:bg-white/10 text-slate-300 transition-colors"
                    aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>

            <nav className={cn("flex-1 py-5 space-y-1 overflow-y-auto", isCollapsed ? "px-2" : "px-3")}>
                {filteredItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={cn(
                            "flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors duration-200 group",
                            isCollapsed && "justify-center",
                            location.pathname === item.path
                                ? "bg-white text-slate-950"
                                : "text-slate-300 hover:bg-white/10 hover:text-white"
                        )}
                    >
                        <item.icon size={20} className={cn(
                            "transition-colors",
                            location.pathname === item.path ? "text-slate-950" : "text-slate-500 group-hover:text-white"
                        )} />
                        {!isCollapsed && <span className="font-medium">{item.name}</span>}
                    </Link>
                ))}
            </nav>

            <div className="p-2 sm:p-3 border-t border-white/10">
                {!isCollapsed && (
                    <div className="mb-3 rounded-md border border-white/10 bg-white/[0.04] p-3">
                        <p className="text-sm font-medium text-white truncate">{user?.name || "Sinh viên"}</p>
                        <p className="text-xs text-slate-400 capitalize">{user?.role?.toLowerCase()}</p>
                    </div>
                )}
                <button
                    onClick={logout}
                    className={cn(
                        "flex items-center gap-3 w-full px-3 py-2.5 rounded-md text-slate-300 hover:bg-red-500/10 hover:text-red-200 transition-colors duration-200 group",
                        isCollapsed && "justify-center"
                    )}
                >
                    <LogOut size={20} className="text-slate-500 group-hover:text-red-200 transition-colors" />
                    {!isCollapsed && <span className="font-medium">Logout</span>}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
