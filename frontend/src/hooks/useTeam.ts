import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teamApi } from '@/services/api';
import type { AddMemberRequest } from '@/types';

export function useTeam() {
  const queryClient = useQueryClient();

  // Get team members
  const {
    data: members = [],
    isLoading: isMembersLoading,
    error: membersError,
  } = useQuery({
    queryKey: ['teamMembers'],
    queryFn: teamApi.getMembers,
    refetchInterval: 60000, // Refetch every minute
  });

  // Get team stats
  const {
    data: stats,
    isLoading: isStatsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ['teamStats'],
    queryFn: teamApi.getStats,
    refetchInterval: 60000,
  });

  // Add member mutation
  const addMemberMutation = useMutation({
    mutationFn: teamApi.addMember,
    onSuccess: () => {
      // Invalidate both members and stats queries
      queryClient.invalidateQueries({ queryKey: ['teamMembers'] });
      queryClient.invalidateQueries({ queryKey: ['teamStats'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  // Remove member mutation
  const removeMemberMutation = useMutation({
    mutationFn: teamApi.removeMember,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teamMembers'] });
      queryClient.invalidateQueries({ queryKey: ['teamStats'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  return {
    // Team members
    members,
    isMembersLoading,
    membersError,

    // Team stats
    stats,
    isStatsLoading,
    statsError,

    // Mutations
    addMember: (data: AddMemberRequest) => addMemberMutation.mutateAsync(data),
    removeMember: (username: string) => removeMemberMutation.mutateAsync(username),
    isAddingMember: addMemberMutation.isPending,
    isRemovingMember: removeMemberMutation.isPending,
    addMemberError: addMemberMutation.error,
    removeMemberError: removeMemberMutation.error,
  };
}
