import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';

export interface StreakData {
    member: string;
    name: string;
    current_streak: number;
    longest_streak: number;
    streak_status: 'active' | 'at_risk' | 'broken' | 'inactive';
    last_active_date: string | null;
    total_active_weeks: number;
    rank?: number;
}

export function useStreaks() {
    return useQuery<StreakData[]>({
        queryKey: ['streaks'],
        queryFn: async () => {
            const response = await api.get('/analytics/streaks');
            return response.data;
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

export function useStreakLeaderboard(limit: number = 10) {
    return useQuery<StreakData[]>({
        queryKey: ['streaks', 'leaderboard', limit],
        queryFn: async () => {
            const response = await api.get(`/analytics/streaks/leaderboard?limit=${limit}`);
            return response.data;
        },
        staleTime: 5 * 60 * 1000,
    });
}

export function useStreaksAtRisk() {
    return useQuery<StreakData[]>({
        queryKey: ['streaks', 'at-risk'],
        queryFn: async () => {
            const response = await api.get('/analytics/streaks/at-risk');
            return response.data;
        },
        staleTime: 5 * 60 * 1000,
    });
}
