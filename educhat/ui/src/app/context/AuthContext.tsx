import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "../services/api";

export type Role = "USER" | "ADMIN" | "student" | "STUDENT";

interface User {
    id: string;
    name: string;
    email: string;
    role: Role;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (credentials: any) => Promise<void>;
    logout: () => void;
    isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem("accessToken");
            if (token) {
                try {
                    // Using /v1/auth/me to get user info
                    const response = await api.get("/v1/auth/me");
                    setUser(response.data);
                } catch (error) {
                    console.error("Failed to fetch user profile", error);
                    localStorage.removeItem("accessToken");
                    localStorage.removeItem("refreshToken");
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = async (credentials: any) => {
        setIsLoading(true);
        try {
            // Map email to username for backend LoginRequest
            const username = credentials.username || credentials.email || "";
            const loginPayload = {
                username: username.includes("@") ? username.split("@")[0] : username,
                password: credentials.password
            };
            const response = await api.post("/v1/login", loginPayload);
            const { access_token, refresh_token, user: userData } = response.data;

            localStorage.setItem("accessToken", access_token);
            localStorage.setItem("refreshToken", refresh_token);
            setUser(userData);
        } catch (error) {
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        setUser(null);
    };

    const value = {
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        isAdmin: user?.role === "ADMIN",
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};
