import { useState, useRef } from 'react';
import { useAnalytics } from '@/hooks/useAnalytics';
import { useTeam } from '@/hooks/useTeam';
import WeeklyProgressChart from '@/components/charts/WeeklyProgressChart';
import AcceptedTrendChart from '@/components/charts/AcceptedTrendChart';
import DifficultyPieChart from '@/components/charts/DifficultyPieChart';
import TeamPerformanceChart from '@/components/charts/TeamPerformanceChart';
import WeekOverWeekTable from '@/components/analytics/WeekOverWeekTable';
import DifficultyDistribution from '@/components/analytics/DifficultyDistribution';
import TeamTagHeatmap from '@/components/analytics/TeamTagHeatmap';
import MemberTagCoverage from '@/components/analytics/MemberTagCoverage';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Camera } from 'lucide-react';
import html2canvas from 'html2canvas';
import { teamApi } from '@/services/api';

export default function Analytics() {
  const [weeks, setWeeks] = useState(12);
  const [trendDays, setTrendDays] = useState(30);
  const [tableWeeks, setTableWeeks] = useState(1);
  const chartsRef = useRef<HTMLDivElement>(null);

  const {
    getWeekOverWeek,
    getWeeklyProgress,
    getAcceptedTrend
  } = useAnalytics();

  const { members, isMembersLoading, isStatsLoading } = useTeam();

  // Fetch data for charts
  const {
    data: weekOverWeek = [],
    isLoading: isWeekOverWeekLoading,
  } = getWeekOverWeek(tableWeeks);

  // Fetch data for charts
  const {
    data: weeklyProgressData,
    isLoading: isWeeklyProgressLoading,
  } = getWeeklyProgress(weeks);

  const {
    data: acceptedTrendData,
    isLoading: isAcceptedTrendLoading,
  } = getAcceptedTrend(trendDays);

  // Filter out suspended members
  const activeMembers = members.filter(m => m.status !== 'suspended');

  // Prepare difficulty pie chart data
  // Note: stats might currently include suspended members if backend get_stats isn't filtered.
  // Ideally, we should recalculate from activeMembers to be consistent if stats is stale/global.
  const activeStats = {
    easy: activeMembers.reduce((sum, m) => sum + m.easy, 0),
    medium: activeMembers.reduce((sum, m) => sum + m.medium, 0),
    hard: activeMembers.reduce((sum, m) => sum + m.hard, 0),
  };

  const difficultyData = [
    { name: 'Easy', value: activeStats.easy },
    { name: 'Medium', value: activeStats.medium },
    { name: 'Hard', value: activeStats.hard },
  ];



  const handleDownloadExcel = async () => {
    try {
      const blob = await teamApi.exportExcel();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `team-data-${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download Excel:', error);
    }
  };

  const isPageLoading =
    isWeekOverWeekLoading ||
    isWeeklyProgressLoading ||
    isAcceptedTrendLoading ||
    isMembersLoading ||
    isStatsLoading;

  const handleCaptureScreenshot = async () => {
    if (isPageLoading) {
      alert("Please wait for all data to load before capturing.");
      return;
    }

    if (chartsRef.current) {
      try {
        // Add a small delay to ensure charts are fully rendered/animated
        await new Promise(resolve => setTimeout(resolve, 1000));

        const canvas = await html2canvas(chartsRef.current, {
          backgroundColor: '#ffffff',
          scale: 2,
          useCORS: true, // Important for external images (avatars)
          logging: false,
          windowWidth: 1920, // Force desktop width
        });

        canvas.toBlob(async (blob) => {
          if (!blob) return;

          const formData = new FormData();
          formData.append('file', blob, `dashboard-${new Date().toISOString().split('T')[0]}.png`);

          try {
            await teamApi.uploadScreenshot(formData);
            alert('Screenshot sent to Discord successfully! 📸');
          } catch (error) {
            console.error('Failed to upload screenshot:', error);
            alert('Failed to send screenshot to Discord.');
          }

          const link = document.createElement('a');
          link.download = `analytics-dashboard-${new Date().toISOString().split('T')[0]}.png`;
          link.href = canvas.toDataURL('image/png');
          link.click();
        }, 'image/png');

      } catch (error) {
        console.error('Failed to capture screenshot:', error);
      }
    }
  };

  return (
    <div className="space-y-6" ref={chartsRef}>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Deep dive into your team's performance
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleCaptureScreenshot}
            disabled={isPageLoading}
          >
            <Camera className="mr-2 h-4 w-4" />
            {isPageLoading ? 'Loading...' : 'Capture'}
          </Button>
          <Button onClick={handleDownloadExcel}>
            <Download className="mr-2 h-4 w-4" />
            Download Excel
          </Button>
        </div>
      </div>

      {/* Week-over-Week Changes */}
      <Card className="glass">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Week-over-Week Changes</CardTitle>
              <CardDescription>
                Compare progress over recent weeks
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {[1, 2, 4].map((w) => (
                <Button
                  key={w}
                  variant={tableWeeks === w ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTableWeeks(w)}
                >
                  Last {w} Week{w > 1 ? 's' : ''}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <WeekOverWeekTable
            data={weekOverWeek}
            isLoading={isWeekOverWeekLoading}
          />
        </CardContent>
      </Card>

      {/* Weekly Progress Chart */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Weekly Progress</h2>
          <div className="flex gap-2">
            {[4, 8, 12, 24].map((w) => (
              <Button
                key={w}
                variant={weeks === w ? 'default' : 'outline'}
                size="sm"
                onClick={() => setWeeks(w)}
              >
                {w} weeks
              </Button>
            ))}
          </div>
        </div>
        <WeeklyProgressChart
          data={weeklyProgressData || null}
          title="Total Solved Over Time"
          description={`Team progress over the last ${weeks} weeks`}
          isLoading={isWeeklyProgressLoading}
        />
      </div>

      {/* Accepted Trend Chart */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Daily Activity</h2>
          <div className="flex gap-2">
            {[7, 30, 90].map((d) => (
              <Button
                key={d}
                variant={trendDays === d ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTrendDays(d)}
              >
                {d} days
              </Button>
            ))}
          </div>
        </div>
        <AcceptedTrendChart
          data={acceptedTrendData ?? null}
          title="Daily Accepted Problems"
          description={`Daily submissions over the last ${trendDays} days`}
          isLoading={isAcceptedTrendLoading}
        />
      </div>

      {/* Team Performance & Difficulty Distribution */}
      <div className="grid gap-6 md:grid-cols-2">
        <TeamPerformanceChart
          members={activeMembers}
          title="Team Performance"
          description="Solved problems breakdown by member"
          isLoading={isMembersLoading}
        />

        <DifficultyPieChart
          data={difficultyData}
          title="Difficulty Distribution"
          description="Breakdown of solved problems by difficulty"
          isLoading={isStatsLoading}
        />
      </div>

      {/* Difficulty Trends & Tag Analysis */}
      <div className="grid gap-6 lg:grid-cols-2">
        <DifficultyDistribution />
        <TeamTagHeatmap />
      </div>

      {/* Member Tag Coverage - Full Width */}
      <MemberTagCoverage />
    </div>
  );
}
