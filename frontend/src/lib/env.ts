const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '');

const deriveWsOriginFromHttp = (httpBase: string) =>
  trimTrailingSlash(httpBase).replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:');

const stripLegacyWsPath = (wsBase: string) => wsBase.replace(/\/api\/v1\/ws\/?$/i, '');

type EnvInput = {
  VITE_API_URL?: string;
  VITE_WS_URL?: string;
  VITE_API_BASE_URL?: string;
  VITE_WS_BASE_URL?: string;
};

export function resolveApiBaseUrl(envInput: EnvInput): string {
  if (envInput.VITE_API_URL) {
    return `${trimTrailingSlash(envInput.VITE_API_URL)}/api/v1`;
  }
  return trimTrailingSlash(envInput.VITE_API_BASE_URL ?? '/api/v1');
}

export function resolveWsBaseUrl(envInput: EnvInput): string {
  if (envInput.VITE_WS_URL) {
    return trimTrailingSlash(envInput.VITE_WS_URL);
  }
  if (envInput.VITE_WS_BASE_URL) {
    return trimTrailingSlash(stripLegacyWsPath(envInput.VITE_WS_BASE_URL));
  }
  if (envInput.VITE_API_URL) {
    return deriveWsOriginFromHttp(envInput.VITE_API_URL);
  }
  if (envInput.VITE_API_BASE_URL?.startsWith('http')) {
    return deriveWsOriginFromHttp(envInput.VITE_API_BASE_URL);
  }
  return 'ws://localhost:8000';
}

const viteEnv = import.meta.env as EnvInput;

export const env = {
  apiBaseUrl: resolveApiBaseUrl(viteEnv),
  wsBaseUrl: resolveWsBaseUrl(viteEnv),
};
