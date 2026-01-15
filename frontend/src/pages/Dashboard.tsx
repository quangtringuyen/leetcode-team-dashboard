import { Users, TrendingUp, Target, Calendar, Flame } from 'lucide-react';
import { useTeam } from '@/hooks/useTeam';
import { useAnalytics } from '@/hooks/useAnalytics';
import { useGamification } from '@/hooks/useGamification';
import { useQuery } from '@tanstack/react-query';
import { settingsApi, apiClient } from '@/services/api';
import StatsCard from '@/components/dashboard/StatsCard';
import Podium from '@/components/dashboard/Podium';
import UnifiedLeaderboard from '@/components/dashboard/UnifiedLeaderboard';
import DailyChallengeCard from '@/components/dashboard/DailyChallengeCard';
import RecentSubmissionsList from '@/components/dashboard/RecentSubmissionsList';
import DailyChallengeCompletions from '@/components/dashboard/DailyChallengeCompletions';
import StreakAtRiskAlert from '@/components/dashboard/StreakAtRiskAlert';
import NotificationCenter from '@/components/dashboard/NotificationCenter';
import StreakCalendar from '@/components/gamification/StreakCalendar';
import AchievementsPanel from '@/components/gamification/AchievementsPanel';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const { members = [], isMembersLoading, isStatsLoading } = useTeam();
  const { recordSnapshot, isRecordingSnapshot, lastSnapshot } = useAnalytics();
  const { streak, achievements, leaderboard: pointsLeaderboard, teamStreak, isLoading: isGamificationLoading } = useGamification();

  // Fetch settings
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.getSettings()
  });

  // Fetch current week's progress (real-time)
  const { data: weeklyProgressData } = useQuery({
    queryKey: ['current-week-progress'],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/current-week-progress');
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

  // Filter out suspended members
  const activeMembers = (members || []).filter(m => m.status !== 'suspended');

  // Calculate stats
  const totalMembers = activeMembers.length;
  const totalSolved = activeMembers.reduce((sum, m) => sum + (m.totalSolved || 0), 0);
  const averageSolved = totalMembers > 0 ? Math.round(totalSolved / totalMembers) : 0;

  // Calculate weekly goal: problems_per_member × number_of_members
  const problemsPerMember = settings?.problems_per_member_weekly || 3;
  const weeklyGoal = totalMembers * problemsPerMember;

  // Get current week's progress from real-time data
  const currentWeekTotal = weeklyProgressData?.current_week_total || 0;
  const weeklyProgress = weeklyGoal > 0 ? Math.min((currentWeekTotal / weeklyGoal) * 100, 100) : 0;
  const weeklyChange = weeklyProgressData?.weekly_change || 0;

  return (
    <div className="max-w-[1600px] mx-auto space-y-8 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pt-2">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-4xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">Dashboard</h1>
            {teamStreak && (
              <div className="flex items-center bg-orange-100 dark:bg-orange-950/40 text-orange-700 dark:text-orange-400 px-3 py-1 rounded-full text-xs font-bold border border-orange-200 dark:border-orange-800 animate-in fade-in slide-in-from-left-2 duration-500">
                <Flame className={`h-3.5 w-3.5 mr-1.5 ${teamStreak.active_today ? 'fill-current animate-pulse' : ''}`} />
                {teamStreak.current_streak} DAY TEAM STREAK
              </div>
            )}
          </div>
          <p className="text-zinc-500 dark:text-zinc-400 max-w-md">
            Real-time performance analytics for your LeetCode team.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={handleRecordSnapshot}
            disabled={isRecordingSnapshot}
            variant="outline"
            className="h-11 px-6 shadow-sm font-semibold"
          >
            <Calendar className="mr-2 h-4 w-4 opacity-70" />
            {isRecordingSnapshot ? 'Recording...' : 'Quick Snapshot'}
          </Button>
        </div>
      </div>

      {lastSnapshot && (
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-sm">
          <p className="text-primary font-medium">
            Snapshot recorded successfully! {lastSnapshot.members_updated} members updated.
          </p>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Team Members"
          value={totalMembers}
          icon={Users}
          description={`${activeMembers.filter((m) => (m.totalSolved || 0) > 0).length} active`}
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

      {/* Main Dash Grid */}
      <div className="grid gap-8 lg:grid-cols-12 items-start">
        {/* Main Column: 8/12 */}
        <div className="lg:col-span-8 space-y-10">
          {/* Top Rankings Area */}
          <div className="grid gap-10">
            <Podium members={activeMembers} isLoading={isMembersLoading} />
            <UnifiedLeaderboard
              problemSolvers={activeMembers.sort((a, b) => (b.totalSolved || 0) - (a.totalSolved || 0))}
              pointEarners={pointsLeaderboard || []}
              isLoading={isMembersLoading || isGamificationLoading}
            />
          </div>

          {/* Bottom Main Content */}
          <div className="pt-6 border-t border-zinc-100 dark:border-zinc-800">
            <AchievementsPanel
              achievements={achievements || []}
              isLoading={isGamificationLoading}
            />
          </div>
        </div>

        {/* Sidebar Column: 4/12 */}
        <div className="lg:col-span-4 space-y-8">
          <StreakCalendar
            currentStreak={streak?.current_streak || 0}
            longestStreak={streak?.longest_streak || 0}
            history={streak?.streak_history || []}
            isLoading={isGamificationLoading}
          />
          <NotificationCenter />
          <DailyChallengeCard />
          <RecentSubmissionsList />
        </div>
      </div>

      {/* Footer Details */}
      <div className="pt-10 border-t border-zinc-100 dark:border-zinc-800 grid gap-10 md:grid-cols-2">
        <div className="space-y-4">
          <h3 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Status Alerts</h3>
          <StreakAtRiskAlert />
        </div>
        <DailyChallengeCompletions />
      </div>
    </div>
  );
}
