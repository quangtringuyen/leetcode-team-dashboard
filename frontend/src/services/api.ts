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
  DailyChallengeHistoryResponse,
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

    const response = await apiClient.post<Token>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};

// ==================== Team Management ====================

export const teamApi = {
  async getMembers(): Promise<TeamMember[]> {
    const response = await apiClient.get<TeamMember[]>('/team/members');
    return response.data;
  },

  async addMember(data: AddMemberRequest): Promise<void> {
    await apiClient.post('/team/members', data);
  },

  async removeMember(username: string): Promise<void> {
    await apiClient.delete(`/team/members/${username}`);
  },

  async getStats(): Promise<TeamStats> {
    const response = await apiClient.get<TeamStats>('/team/stats');
    return response.data;
  },

  async exportExcel(): Promise<Blob> {
    const response = await apiClient.get('/team/export/excel', {
      responseType: 'blob',
    });
    return response.data;
  },

  async backup(): Promise<any> {
    const response = await apiClient.get('/team/backup');
    return response.data;
  },

  async restore(backup: any): Promise<void> {
    await apiClient.post('/team/restore', backup);
  },

  async uploadScreenshot(formData: FormData): Promise<void> {
    await apiClient.post('/notifications/upload-screenshot', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// ==================== Analytics ====================

export const analyticsApi = {
  async getHistory(): Promise<WeeklySnapshot[]> {
    const response = await apiClient.get<WeeklySnapshot[]>('/analytics/history');
    return response.data;
  },

  async recordSnapshot(): Promise<SnapshotResponse> {
    const response = await apiClient.post<SnapshotResponse>('/analytics/snapshot');
    return response.data;
  },

  async getTrends(weeks: number = 12): Promise<TrendData> {
    const response = await apiClient.get<TrendData>('/analytics/trends', {
      params: { weeks },
    });
    return response.data;
  },

  async getWeekOverWeek(weeks: number = 1): Promise<WeekOverWeekChange[]> {
    const response = await apiClient.get<WeekOverWeekChange[]>('/analytics/week-over-week', {
      params: { weeks },
    });
    return response.data;
  },

  async getWeeklyProgress(weeks: number = 12): Promise<WeeklyProgressData> {
    const response = await apiClient.get('/analytics/weekly-progress', {
      params: { weeks }
    });
    return response.data;
  },

  async getAcceptedTrend(days: number = 30): Promise<AcceptedTrendData[]> {
    const response = await apiClient.get('/analytics/accepted-trend', {
      params: { days },
    });
    return response.data;
  },
};

export const leetcodeApi = {
  async getDailyChallenge(): Promise<DailyChallenge> {
    const response = await apiClient.get('/leetcode/daily');
    return response.data;
  },

  async getDailyCompletions(): Promise<{
    challenge: DailyChallenge;
    completions: Array<{
      username: string;
      name: string;
      avatar: string | null;
      completed: boolean;
      completionTime: string | null;
    }>;
    totalMembers: number;
    completedCount: number;
  }> {
    const response = await apiClient.get('/leetcode/daily/completions');
    return response.data;
  },

  async getRecentSubmissions(limit: number = 20): Promise<RecentSubmission[]> {
    const response = await apiClient.get('/leetcode/recent', {
      params: { limit },
    });
    return response.data;
  },

  async getDailyHistory(days: number = 7): Promise<DailyChallengeHistoryResponse> {
    const response = await apiClient.get('/leetcode/daily/history', {
      params: { days },
    });
    return response.data;
  },
};

export const notificationsApi = {
  async getLogs(limit: number = 50, offset: number = 0, status?: string): Promise<{
    notifications: any[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const response = await apiClient.get('/notifications-log', {
      params: { limit, offset, status },
    });
    return response.data;
  },

  async resend(id: number): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`/notifications-log/${id}/resend`);
    return response.data;
  },

  async checkSubmissions(): Promise<{ notifications: any[]; count: number; message: string }> {
    const response = await apiClient.post('/notifications/check-submissions');
    return response.data;
  },
};

// ==================== Health Check ====================

export const healthApi = {
  async check(): Promise<{ status: string; storage: string }> {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default apiClient;
