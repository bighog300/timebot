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
