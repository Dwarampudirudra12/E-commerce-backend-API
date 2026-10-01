import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import * as authApi from "../api/authApi.js";
import { me as fetchMe } from "../api/usersApi.js";
import { homeFor } from "../constants/roles.js";

const AuthContext = createContext(null);

function readTokens() {
  try {
    return JSON.parse(localStorage.getItem("ecom_tokens") || "null");
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [tokens, setTokens] = useState(readTokens);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!readTokens());
  const [apiOnline, setApiOnline] = useState(null);

  const loadUser = useCallback(async () => {
    try {
      const u = await fetchMe();
      setUser(u);
      return u;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    if (!tokens) {
      setLoading(false);
      return;
    }
    setLoading(true);
    loadUser().finally(() => setLoading(false));
    const onExpired = () => {
      setTokens(null);
      setUser(null);
    };
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, [tokens, loadUser]);

  const signIn = useCallback(
    async (email, password) => {
      const t = await authApi.login(email, password);
      localStorage.setItem("ecom_tokens", JSON.stringify(t));
      setTokens(t);
      const u = await loadUser();
      return { tokens: t, user: u, home: homeFor(u?.role) };
    },
    [loadUser]
  );

  const signUp = useCallback((payload) => authApi.register(payload), []);

  const signOut = useCallback(async () => {
    const t = readTokens();
    try {
      if (t?.refresh_token) await authApi.logout(t.refresh_token);
    } catch {
      /* best effort */
    }
    localStorage.removeItem("ecom_tokens");
    setTokens(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      tokens, user, loading,
      role: user?.role || "GUEST",
      isAuthed: !!user,
      apiOnline, setApiOnline,
      signIn, signUp, signOut, reloadUser: loadUser,
    }),
    [tokens, user, loading, apiOnline, signIn, signUp, signOut, loadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
