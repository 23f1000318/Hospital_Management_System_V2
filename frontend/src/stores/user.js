import { defineStore } from "pinia";
import api from "@/utils/api";

export const useUserStore = defineStore("user", {
  state: () => ({
    token: localStorage.getItem("access_token") || null,
    user: (() => {
      try {
        const raw = localStorage.getItem("user");
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        console.warn("Failed to parse stored user", e);
        return null;
      }
    })(),
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    role: (state) => (state.user && state.user.role ? state.user.role : null),
    isAdmin: (state) => state.user?.role === "admin",
    isDoctor: (state) => state.user?.role === "doctor",
    isPatient: (state) => state.user?.role === "patient",
  },

  actions: {
    setToken(token) {
      this.token = token;
      if (token) {
        localStorage.setItem("access_token", token);
      } else {
        localStorage.removeItem("access_token");
      }
    },

    setUser(user) {
      this.user = user;
      if (user) {
        try {
          localStorage.setItem("user", JSON.stringify(user));
        } catch (e) {
          console.warn("Failed to serialize user for storage", e);
        }
      } else {
        localStorage.removeItem("user");
      }
    },

    logout() {
      this.setToken(null);
      this.setUser(null);
    },

    async loginWithCredentials(credentials = {}) {
      const res = await api.post("/auth/login", credentials);
      
      const token = res.token;
      if (!token) {
        throw new Error("Login response did not include a token");
      }

      this.setToken(token);
      this.setUser(res);
      return res;
    },
  },
});
