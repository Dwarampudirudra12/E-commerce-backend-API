import { createContext, useContext, useMemo } from "react";
import { can } from "../constants/roles.js";
import { useAuth } from "./AuthContext.jsx";

const PermissionContext = createContext(null);

export function PermissionProvider({ children }) {
  const { role } = useAuth();
  const value = useMemo(
    () => ({ role, can: (capability) => can(role, capability) }),
    [role]
  );
  return <PermissionContext.Provider value={value}>{children}</PermissionContext.Provider>;
}

export const usePermissions = () => useContext(PermissionContext);
