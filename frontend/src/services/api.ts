/**
 * API Client for LeetCode Team Dashboard
 * Axios instance with JWT token management
 */

import axios, { AxiosError } from 'axios';
import type {
  User,
  LoginRequest,
  RegisterRequest,
  Token,
  TeamMember,
  AddMemberRequest,
  TeamStats,
  WeeklySnapshot,
  TrendData,
  WeekOverWeekChange,
  SnapshotResponse,
  ApiError,
  WeeklyProgressData,
  AcceptedTrendData,
  DailyChallenge,
  RecentSubmission,
} from '@/types';

// Use same host as frontend, but on port 8090
const getApiBaseUrl = () => {
  // If VITE_API_URL is explicitly set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Otherwise, use current hostname with port 8090
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  return `${protocol}//${hostname}:8090`;
};

const API_BASE_URL = getApiBaseUrl();

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==================== Authentication ====================

export const authApi = {
  async login(data: LoginRequest): Promise<Token> {
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await apiClient.post<Token>('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>('/api/auth/register', data);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me');
    return response.data;
  },
};

// ==================== Team Management ====================

export const teamApi = {
  async getMembers(): Promise<TeamMember[]> {
    const response = await apiClient.get<TeamMember[]>('/api/team/members');
    return response.data;
  },

  async addMember(data: AddMemberRequest): Promise<void> {
    await apiClient.post('/api/team/members', data);
  },

  async removeMember(username: string): Promise<void> {
    await apiClient.delete(`/api/team/members/${username}`);
  },

  async getStats(): Promise<TeamStats> {
    const response = await apiClient.get<TeamStats>('/api/team/stats');
    return response.data;
  },

  async exportExcel(): Promise<Blob> {
    const response = await apiClient.get('/api/team/export/excel', {
      responseType: 'blob',
    });
    return response.data;
  },

  async backup(): Promise<any> {
    const response = await apiClient.get('/api/team/backup');
    return response.data;
  },

  async restore(backup: any): Promise<void> {
    await apiClient.post('/api/team/restore', backup);
  },
};

// ==================== Analytics ====================

export const analyticsApi = {
  async getHistory(): Promise<WeeklySnapshot[]> {
    const response = await apiClient.get<WeeklySnapshot[]>('/api/analytics/history');
    return response.data;
  },

  async recordSnapshot(): Promise<SnapshotResponse> {
    const response = await apiClient.post<SnapshotResponse>('/api/analytics/snapshot');
    return response.data;
  },

  async getTrends(weeks: number = 12): Promise<TrendData> {
    const response = await apiClient.get<TrendData>('/api/analytics/trends', {
      params: { weeks },
    });
    return response.data;
  },

  async getWeekOverWeek(): Promise<WeekOverWeekChange[]> {
    const response = await apiClient.get<WeekOverWeekChange[]>('/api/analytics/week-over-week');
    return response.data;
  },

  async getWeeklyProgress(weeks: number = 12): Promise<WeeklyProgressData> {
    const response = await apiClient.get('/api/analytics/weekly-progress', {
      params: { weeks }
    });
    return response.data;
  },

  async getAcceptedTrend(days: number = 30): Promise<AcceptedTrendData[]> {
    const response = await apiClient.get('/api/analytics/accepted-trend', {
      params: { days },
    });
    return response.data;
  },
};

export const leetcodeApi = {
  async getDailyChallenge(): Promise<DailyChallenge> {
    const response = await apiClient.get('/api/leetcode/daily');
    return response.data;
  },

  async getRecentSubmissions(limit: number = 20): Promise<RecentSubmission[]> {
    const response = await apiClient.get('/api/leetcode/recent', {
      params: { limit },
    });
    return response.data;
  },
};

// ==================== Health Check ====================

export const healthApi = {
  async check(): Promise<{ status: string; storage: string }> {
    const response = await apiClient.get('/api/health');
    return response.data;
  },
};

export default apiClient;
