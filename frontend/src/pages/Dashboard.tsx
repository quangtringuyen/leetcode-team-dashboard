import { Users, TrendingUp, Target, Calendar } from 'lucide-react';
import { useTeam } from '@/hooks/useTeam';
import { useAnalytics } from '@/hooks/useAnalytics';
import StatsCard from '@/components/dashboard/StatsCard';
import Podium from '@/components/dashboard/Podium';
import Leaderboard from '@/components/dashboard/Leaderboard';
import DailyChallengeCard from '@/components/dashboard/DailyChallengeCard';
import RecentSubmissionsList from '@/components/dashboard/RecentSubmissionsList';
import DailyChallengeCompletions from '@/components/dashboard/DailyChallengeCompletions';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const { members, stats, isMembersLoading, isStatsLoading } = useTeam();
  const { recordSnapshot, isRecordingSnapshot, lastSnapshot } = useAnalytics();

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
  const weeklyGoal = 100; // Could be configurable
  const goalProgress = Math.min((totalSolved / weeklyGoal) * 100, 100);

  return (
    <div className="space-y-6">
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
          value={`${goalProgress.toFixed(0)}%`}
          icon={Calendar}
          description={`${totalSolved}/${weeklyGoal} problems`}
          trend={{
            value: goalProgress,
            isPositive: goalProgress >= 50,
          }}
          isLoading={isStatsLoading}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Leaderboard & Podium */}
        <div className="lg:col-span-2 space-y-6">
          <Podium members={members} isLoading={isMembersLoading} />
          <Leaderboard members={members} isLoading={isMembersLoading} />
        </div>

        {/* Right Column: Daily Challenge & Recent Activity */}
        <div className="space-y-6">
          <DailyChallengeCard />
          <RecentSubmissionsList />
        </div>
      </div>

      {/* Daily Challenge Completions - Full Width at Bottom */}
      <DailyChallengeCompletions />
    </div>
  );
}
