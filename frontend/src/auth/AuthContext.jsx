import { useState } from "react";
import api from "../api/client";
import { AuthContext } from "./context";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("edubridge_user")); }
    catch { return null; }
  });

  function establishSession(data) {
    localStorage.setItem("edubridge_token", data.access_token);
    localStorage.setItem("edubridge_user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }

  async function login(email, password) {
    const { data } = await api.post("/auth/login", { email, password });
    return establishSession(data);
  }

  async function register(name, email, password, language) {
    const { data } = await api.post("/auth/register", { name, email, password, language });
    return establishSession(data);
  }

  function logout() {
    localStorage.removeItem("edubridge_token");
    localStorage.removeItem("edubridge_user");
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, login, register, logout }}>{children}</AuthContext.Provider>;
}