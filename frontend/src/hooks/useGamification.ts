import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

export interface StreakData {
    current_streak: number;
    longest_streak: number;
    streak_history: string[];
}

export interface PointsData {
    current: number;
    weekly: number;
    monthly: number;
    all_time: number;
}

export interface LeaderboardEntry {
    rank: number;
    username: string;
    points: number;
}

export interface Achievement {
    key: string;
    name: string;
    description: string;
    icon: string;
    category: string;
    unlocked: boolean;
    unlocked_at?: string;
}

export const useGamification = () => {
    const { data: streak, isLoading: isStreakLoading } = useQuery({
        queryKey: ['gamification-streak'],
        queryFn: async () => {
            const response = await apiClient.get<StreakData>('/gamification/streak');
            return response.data;
        },
    });

    const { data: points, isLoading: isPointsLoading } = useQuery({
        queryKey: ['gamification-points'],
        queryFn: async () => {
            const response = await apiClient.get<PointsData>('/gamification/points');
            return response.data;
        },
    });

    const { data: achievements, isLoading: isAchievementsLoading } = useQuery({
        queryKey: ['gamification-achievements'],
        queryFn: async () => {
            const response = await apiClient.get<Achievement[]>('/gamification/achievements');
            return response.data;
        },
    });

    const { data: leaderboard, isLoading: isLeaderboardLoading } = useQuery({
        queryKey: ['gamification-leaderboard'],
        queryFn: async () => {
            const response = await apiClient.get<LeaderboardEntry[]>('/gamification/leaderboard?period=weekly');
            return response.data;
        },
    });

    return {
        streak,
        points,
        achievements,
        leaderboard,
        isLoading: isStreakLoading || isPointsLoading || isAchievementsLoading || isLeaderboardLoading
    };
};
