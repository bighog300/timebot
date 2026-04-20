import axios from 'axios';
import { env } from '@/lib/env';

export const http = axios.create({
  baseURL: env.apiBaseUrl,
});
