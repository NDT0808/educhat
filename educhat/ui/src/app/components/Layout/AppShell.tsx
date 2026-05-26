import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

const AppShell: React.FC = () => {
    const [isCollapsed, setIsCollapsed] = useState(() => {
        if (typeof window === "undefined") return false;
        return window.innerWidth < 768;
    });

    return (
        <div className="flex h-screen bg-[#f6f8fb] overflow-hidden font-sans text-slate-900">
            <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />

            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <Topbar />

                <main className="flex-1 overflow-y-auto relative">
                    <div className="relative z-10 h-full p-4 sm:p-6 lg:p-8">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default AppShell;
