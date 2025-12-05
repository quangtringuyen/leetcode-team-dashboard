import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';

export interface TagAnalysis {
    member: string;
    name: string;
    tag_counts: Record<string, number>;
    total_unique_tags: number;
    top_tags: Array<{
        tag: string;
        count: number;
        percentage: number;
    }>;
    weak_tags: Array<{
        tag: string;
        count: number;
        recommendation: string;
    }>;
    coverage_score: number;
    recommendation: string;
}

export interface TeamHeatmap {
    team_strengths: Array<{
        tag: string;
        count: number;
        percentage: number;
    }>;
    team_weaknesses: Array<{
        tag: string;
        count: number;
        recommendation: string;
    }>;
    team_coverage_score: number;
    total_unique_tags: number;
    total_problems: number;
}

export interface TagRecommendations {
    member: string;
    weak_tags: Array<{
        tag: string;
        count: number;
        recommendation: string;
    }>;
    recommendations: Array<{
        tag: string;
        difficulty: string;
        reason: string;
        search_query: string;
    }>;
    coverage_score: number;
}

export function useTagAnalysis(limit: number = 100) {
    return useQuery<TagAnalysis[]>({
        queryKey: ['tags', 'analysis', limit],
        queryFn: async () => {
            const response = await api.get(`/analytics/tags/analysis?limit=${limit}`);
            return response.data;
        },
        staleTime: 10 * 60 * 1000, // 10 minutes (tag fetching is slow)
    });
}

export function useTeamHeatmap(limit: number = 100) {
    return useQuery<TeamHeatmap>({
        queryKey: ['tags', 'heatmap', limit],
        queryFn: async () => {
            const response = await api.get(`/analytics/tags/heatmap?limit=${limit}`);
            return response.data;
        },
        staleTime: 10 * 60 * 1000,
    });
}

export function useTagRecommendations(
    memberUsername: string,
    difficulty: string = 'medium',
    limit: number = 100
) {
    return useQuery<TagRecommendations>({
        queryKey: ['tags', 'recommendations', memberUsername, difficulty, limit],
        queryFn: async () => {
            const response = await api.get(
                `/analytics/tags/recommendations/${memberUsername}?difficulty=${difficulty}&limit=${limit}`
            );
            return response.data;
        },
        enabled: !!memberUsername,
        staleTime: 10 * 60 * 1000,
    });
}
