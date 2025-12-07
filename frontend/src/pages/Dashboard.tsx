import { Users, TrendingUp, Target, Calendar } from 'lucide-react';
import { useTeam } from '@/hooks/useTeam';
import { useAnalytics } from '@/hooks/useAnalytics';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import StatsCard from '@/components/dashboard/StatsCard';
import Podium from '@/components/dashboard/Podium';
import Leaderboard from '@/components/dashboard/Leaderboard';
import DailyChallengeCard from '@/components/dashboard/DailyChallengeCard';
import RecentSubmissionsList from '@/components/dashboard/RecentSubmissionsList';
import DailyChallengeCompletions from '@/components/dashboard/DailyChallengeCompletions';
import StreakLeaderboard from '@/components/dashboard/StreakLeaderboard';
import StreakAtRiskAlert from '@/components/dashboard/StreakAtRiskAlert';
import NotificationCenter from '@/components/dashboard/NotificationCenter';
import { Button } from '@/components/ui/button';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const { members, stats, isMembersLoading, isStatsLoading } = useTeam();
  const { recordSnapshot, isRecordingSnapshot, lastSnapshot } = useAnalytics();

  // Fetch settings
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  });

  // Fetch current week's progress (real-time)
  const { data: weeklyProgressData } = useQuery({
    queryKey: ['current-week-progress'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/analytics/current-week-progress`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  const handleRecordSnapshot = async () => {
    try {
      await recordSnapshot();
    } catch (error) {
      console.error('Failed to record snapshot:', error);
    }
  };

  // Calculate stats
  const totalMembers = members.length;
  const totalSolved = stats?.total_problems_solved || 0;
  const averageSolved = totalMembers > 0 ? Math.round(totalSolved / totalMembers) : 0;

  // Calculate weekly goal: problems_per_member × number_of_members
  const problemsPerMember = settings?.problems_per_member_weekly || 3;
  const weeklyGoal = totalMembers * problemsPerMember;

  // Get current week's progress from real-time data
  const currentWeekTotal = weeklyProgressData?.current_week_total || 0;
  const weeklyProgress = weeklyGoal > 0 ? Math.min((currentWeekTotal / weeklyGoal) * 100, 100) : 0;
  const weeklyChange = weeklyProgressData?.weekly_change || 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Track your team's LeetCode progress
          </p>
        </div>
        <Button
          onClick={handleRecordSnapshot}
          disabled={isRecordingSnapshot}
          className="gap-2"
        >
          <Calendar className="h-4 w-4" />
          {isRecordingSnapshot ? 'Recording...' : 'Record Snapshot'}
        </Button>
      </div>

      {lastSnapshot && (
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-sm">
          <p className="text-primary font-medium">
            Snapshot recorded successfully! {lastSnapshot.members_updated} members updated.
          </p>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Team Members"
          value={totalMembers}
          icon={Users}
          description={`${members.filter((m) => m.totalSolved > 0).length} active`}
          isLoading={isMembersLoading}
        />
        <StatsCard
          title="Total Solved"
          value={totalSolved}
          icon={Target}
          description="All time problems"
          isLoading={isStatsLoading}
        />
        <StatsCard
          title="Average Solved"
          value={averageSolved}
          icon={TrendingUp}
          description="Per team member"
          isLoading={isStatsLoading}
        />
        <StatsCard
          title="Weekly Goal"
          value={`${weeklyProgress.toFixed(0)}%`}
          icon={Calendar}
          description={`${currentWeekTotal}/${weeklyGoal} problems`}
          trend={{
            value: weeklyChange,
            isPositive: weeklyChange >= 0,
          }}
          isLoading={isStatsLoading}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left Column: Leaderboard & Podium */}
        <div className="lg:col-span-2 space-y-8">
          <Podium members={members} isLoading={isMembersLoading} />
          <Leaderboard members={members} isLoading={isMembersLoading} />
        </div>

        {/* Right Column: Notifications, Streaks, Daily Challenge & Recent Activity */}
        <div className="space-y-6">
          <NotificationCenter />
          <StreakAtRiskAlert />
          <StreakLeaderboard />
          <DailyChallengeCard />
          <RecentSubmissionsList />
        </div>
      </div>

      {/* Daily Challenge Completions - Full Width at Bottom */}
      <DailyChallengeCompletions />
    </div>
  );
}
