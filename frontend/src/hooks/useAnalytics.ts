import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analyticsApi } from '@/services/api';

export function useAnalytics() {
  const queryClient = useQueryClient();

  // Get weekly history
  const {
    data: history = [],
    isLoading: isHistoryLoading,
    error: historyError,
  } = useQuery({
    queryKey: ['analytics', 'history'],
    queryFn: analyticsApi.getHistory,
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  // Get trends data (Legacy)
  const getTrends = (weeks: number = 12) =>
    useQuery({
      queryKey: ['analytics', 'trends', weeks],
      queryFn: () => analyticsApi.getTrends(weeks),
      refetchInterval: 300000,
    });

  // Get weekly progress (New)
  const getWeeklyProgress = (weeks: number = 12) =>
    useQuery({
      queryKey: ['analytics', 'weeklyProgress', weeks],
      queryFn: () => analyticsApi.getWeeklyProgress(weeks),
      refetchInterval: 300000,
    });

  // Get accepted trend (New)
  const getAcceptedTrend = (days: number = 30) =>
    useQuery({
      queryKey: ['analytics', 'acceptedTrend', days],
      queryFn: () => analyticsApi.getAcceptedTrend(days),
      refetchInterval: 300000,
    });

  // Get week-over-week changes
  const {
    data: weekOverWeek = [],
    isLoading: isWeekOverWeekLoading,
    error: weekOverWeekError,
  } = useQuery({
    queryKey: ['analytics', 'weekOverWeek'],
    queryFn: analyticsApi.getWeekOverWeek,
    refetchInterval: 300000,
  });

  // Record snapshot mutation
  const recordSnapshotMutation = useMutation({
    mutationFn: analyticsApi.recordSnapshot,
    onSuccess: () => {
      // Invalidate all analytics queries
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      queryClient.invalidateQueries({ queryKey: ['teamMembers'] });
      queryClient.invalidateQueries({ queryKey: ['teamStats'] });
    },
  });

  return {
    // History
    history,
    isHistoryLoading,
    historyError,

    // Trends
    getTrends,
    getWeeklyProgress,
    getAcceptedTrend,

    // Week over week
    weekOverWeek,
    isWeekOverWeekLoading,
    weekOverWeekError,

    // Snapshot
    recordSnapshot: () => recordSnapshotMutation.mutateAsync(),
    isRecordingSnapshot: recordSnapshotMutation.isPending,
    recordSnapshotError: recordSnapshotMutation.error,
    lastSnapshot: recordSnapshotMutation.data,
  };
}
