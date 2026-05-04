import axios from 'axios';
import { env } from '@/lib/env';

export const http = axios.create({
  baseURL: env.apiBaseUrl,
});


export const WORKSPACE_STORAGE_KEY = "activeWorkspaceId";
http.interceptors.request.use((config) => {
  const workspaceId = typeof window !== "undefined" ? localStorage.getItem(WORKSPACE_STORAGE_KEY) : null;
  if (workspaceId) {
    config.headers = config.headers || {};
    config.headers["X-Workspace-ID"] = workspaceId;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail;
    if ((error?.response?.status === 403 || error?.response?.status === 404) && typeof detail === "string" && detail.toLowerCase().includes("workspace")) {
      if (typeof window !== "undefined") localStorage.removeItem(WORKSPACE_STORAGE_KEY);
    }
    return Promise.reject(error);
  }
);
