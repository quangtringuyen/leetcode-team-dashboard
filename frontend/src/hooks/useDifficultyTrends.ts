import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';

export interface DifficultyTrend {
    week: string;
    easy: number;
    medium: number;
    hard: number;
    total: number;
    easy_pct: number;
    medium_pct: number;
    hard_pct: number;
}

export interface DifficultyAnalysis {
    member: string;
    name: string;
    trends: DifficultyTrend[];
    current_distribution: {
        easy: number;
        medium: number;
        hard: number;
        easy_pct: number;
        medium_pct: number;
        hard_pct: number;
    };
    progression_status: string;
    stuck_on_difficulty: string | null;
    recommendation: string;
}

export function useDifficultyTrends() {
    return useQuery<DifficultyAnalysis[]>({
        queryKey: ['difficulty-trends'],
        queryFn: async () => {
            const response = await api.get('/api/analytics/difficulty-trends');
            return response.data;
        },
        staleTime: 5 * 60 * 1000,
    });
}

export function useStuckMembers() {
    return useQuery<DifficultyAnalysis[]>({
        queryKey: ['difficulty-trends', 'stuck'],
        queryFn: async () => {
            const response = await api.get('/api/analytics/difficulty-trends/stuck');
            return response.data;
        },
        staleTime: 5 * 60 * 1000,
    });
}
