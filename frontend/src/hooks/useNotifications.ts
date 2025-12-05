import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';

export interface Notification {
    type: string;
    member?: string;
    member_name?: string;
    title: string;
    message: string;
    priority: string;
    action?: string;
    created_at: string;
    read?: boolean;
}

export interface NotificationSettings {
    email_enabled: boolean;
    slack_enabled: boolean;
    discord_enabled: boolean;
    in_app_enabled: boolean;
    streak_alerts: boolean;
    milestone_celebrations: boolean;
    daily_digest: boolean;
    inactivity_reminders: boolean;
}

export function useNotifications(limit: number = 50) {
    return useQuery<{ notifications: Notification[]; count: number; unread_count: number }>({
        queryKey: ['notifications', limit],
        queryFn: async () => {
            const response = await api.get(`/api/notifications?limit=${limit}`);
            return response.data;
        },
        refetchInterval: 60000, // Refetch every minute
    });
}

export function useCheckStreakNotifications() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            const response = await api.post('/api/notifications/check-streaks');
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
        },
    });
}

export function useSendDailyDigest() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            const response = await api.post('/api/notifications/send-digest');
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
        },
    });
}

export function useCheckSubmissions() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            const response = await api.post('/api/notifications/check-submissions');
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
        },
    });
}

export function useClearNotifications() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            const response = await api.delete('/api/notifications');
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
        },
    });
}

export function useNotificationSettings() {
    return useQuery<NotificationSettings>({
        queryKey: ['notification-settings'],
        queryFn: async () => {
            const response = await api.get('/api/notifications/settings');
            return response.data;
        },
    });
}
