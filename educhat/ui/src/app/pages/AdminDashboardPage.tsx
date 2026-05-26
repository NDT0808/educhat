import React from "react";
import { Users, FileText, Globe, Activity } from "lucide-react";

const AdminDashboardPage: React.FC = () => {
    const stats = [
        { label: "Active Users", value: "1,234", icon: Users, color: "bg-blue-500" },
        { label: "Total Prompts", value: "56", icon: FileText, color: "bg-indigo-500" },
        { label: "Knowledge Docs", value: "892", icon: Globe, color: "bg-violet-500" },
        { label: "System Uptime", value: "99.9%", icon: Activity, color: "bg-emerald-500" },
    ];

    return (
        <div className="space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat) => (
                    <div key={stat.label} className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
                        <div className="flex items-center gap-4">
                            <div className={`${stat.color} p-3 rounded-2xl text-white shadow-lg`}>
                                <stat.icon size={24} />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                                <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm min-h-[400px] flex flex-col items-center justify-center text-center">
                    <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center text-slate-300 mb-6">
                        <Users size={40} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-2">User Management</h3>
                    <p className="text-slate-500 max-w-sm">Manage user accounts, roles, and access permissions from this module (Upcoming feature).</p>
                </div>

                <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm min-h-[400px] flex flex-col items-center justify-center text-center">
                    <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center text-slate-300 mb-6">
                        <FileText size={40} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-2">Prompt Engineering</h3>
                    <p className="text-slate-500 max-w-sm">Configure and version LLM prompts and system instructions (Upcoming feature).</p>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboardPage;
