import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth, Role } from "../context/AuthContext";

interface RoleGuardProps {
    children: React.ReactNode;
    allowedRoles: Role[];
}

const RoleGuard: React.FC<RoleGuardProps> = ({ children, allowedRoles }) => {
    const { user, isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return null; // Or a smaller spinner
    }

    if (!isAuthenticated || !user || !allowedRoles.includes(user.role)) {
        return <Navigate to="/" replace />;
    }

    return <>{children}</>;
};

export default RoleGuard;
