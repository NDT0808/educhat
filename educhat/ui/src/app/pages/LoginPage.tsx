import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useLocation } from "react-router-dom";
import { LogIn, Mail, Lock, AlertCircle, Eye, EyeOff, GraduationCap } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { cn } from "../utils/cn";

const LoginPage: React.FC = () => {
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const { register, handleSubmit, formState: { errors } } = useForm();
    const from = location.state?.from?.pathname || "/";

    const onSubmit = async (data: any) => {
        setIsLoading(true);
        setError(null);
        try {
            await login(data);
            navigate(from, { replace: true });
        } catch (err: any) {
            setError(err.response?.data?.message || "Thông tin đăng nhập chưa đúng. Vui lòng thử lại.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen grid lg:grid-cols-[1.05fr_0.95fr] bg-[#f6f8fb]">
            <section className="hidden lg:flex flex-col justify-between border-r border-slate-200 bg-slate-950 p-10 text-white">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-md bg-white text-slate-950">
                        <GraduationCap size={22} />
                    </div>
                    <div>
                        <p className="text-lg font-semibold">EduChat</p>
                        <p className="text-xs text-slate-400">Academic planning assistant</p>
                    </div>
                </div>

                <div className="max-w-xl">
                    <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Student workspace</p>
                    <h1 className="text-4xl font-semibold leading-tight tracking-tight">
                        Tư vấn tuyển sinh, lộ trình học và thời khóa biểu trong một nơi.
                    </h1>
                    <p className="mt-5 text-base leading-7 text-slate-300">
                        Đăng nhập để tra cứu thông tin học tập, lập kế hoạch môn học và kiểm tra lịch biểu cá nhân.
                    </p>
                </div>

                <div className="grid grid-cols-3 gap-3 text-sm">
                    {["Tư vấn", "Planner", "Timetable"].map((item) => (
                        <div key={item} className="rounded-md border border-white/10 bg-white/[0.04] px-4 py-3 text-slate-300">
                            {item}
                        </div>
                    ))}
                </div>
            </section>

            <section className="flex min-h-screen items-center justify-center p-4 sm:p-6">
                <div className="w-full max-w-md">
                    <div className="mb-8 lg:hidden flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-slate-950 text-white">
                            <GraduationCap size={22} />
                        </div>
                        <div>
                            <p className="text-lg font-semibold text-slate-950">EduChat</p>
                            <p className="text-xs text-slate-500">Academic assistant</p>
                        </div>
                    </div>

                    <div className="bg-white border border-slate-200 rounded-lg p-6 sm:p-8 shadow-sm">
                    <div className="mb-8">
                        <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white mb-5">
                            <LogIn size={21} />
                        </div>
                        <h1 className="text-2xl font-semibold text-slate-950 mb-2">Đăng nhập</h1>
                        <p className="text-slate-500 font-medium">Sử dụng tài khoản sinh viên để tiếp tục</p>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Username (Mã sinh viên)</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-slate-700 transition-colors">
                                    <Mail size={18} />
                                </div>
                                <input
                                    {...register("username", { required: "Username is required" })}
                                    type="text"
                                    className={cn(
                                        "w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-md focus:ring-2 focus:ring-slate-100 focus:border-slate-600 outline-none transition-colors font-medium",
                                        errors['username'] && "border-red-300 bg-red-50/50 focus:ring-red-100 focus:border-red-500"
                                    )}
                                    placeholder="Nhập mã sinh viên (ví dụ: YD2024001)"
                                />
                            </div>
                            {errors['username'] && <p className="text-xs text-red-500 font-semibold">{errors['username']?.message as string}</p>}
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Password</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-slate-700 transition-colors">
                                    <Lock size={18} />
                                </div>
                                <input
                                    {...register("password", { required: "Password is required" })}
                                    type={showPassword ? "text" : "password"}
                                    className={cn(
                                        "w-full pl-10 pr-12 py-3 bg-white border border-slate-200 rounded-md focus:ring-2 focus:ring-slate-100 focus:border-slate-600 outline-none transition-colors font-medium",
                                        errors['password'] && "border-red-300 bg-red-50/50 focus:ring-red-100 focus:border-red-500"
                                    )}
                                    placeholder="Mat khau"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            {errors['password'] && <p className="text-xs text-red-500 font-semibold">{errors['password']?.message as string}</p>}
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-3 bg-red-50 text-red-600 rounded-md border border-red-100 text-sm font-semibold">
                                <AlertCircle size={18} />
                                <span>{error}</span>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3 bg-slate-950 hover:bg-slate-800 text-white rounded-md font-semibold text-base transition-colors disabled:opacity-70 flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                "Sign In"
                            )}
                        </button>
                    </form>

                    <p className="mt-6 text-center text-sm font-medium text-slate-500">
                        Chưa có tài khoản?{" "}
                        <a href="#" className="text-slate-900 font-semibold hover:underline">Liên hệ quản trị viên</a>
                    </p>
                </div>
            </div>
            </section>
        </div>
    );
};

export default LoginPage;
