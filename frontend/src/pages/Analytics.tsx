import { useState, useRef } from 'react';
import { useAnalytics } from '@/hooks/useAnalytics';
import { useTeam } from '@/hooks/useTeam';
import WeeklyProgressChart from '@/components/charts/WeeklyProgressChart';
import AcceptedTrendChart from '@/components/charts/AcceptedTrendChart';
import DifficultyPieChart from '@/components/charts/DifficultyPieChart';
import TeamPerformanceChart from '@/components/charts/TeamPerformanceChart';
import WeekOverWeekTable from '@/components/analytics/WeekOverWeekTable';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Camera } from 'lucide-react';
import html2canvas from 'html2canvas';

export default function Analytics() {
  const [weeks, setWeeks] = useState(12);
  const [trendDays, setTrendDays] = useState(30);
  const chartsRef = useRef<HTMLDivElement>(null);

  const {
    weekOverWeek,
    isWeekOverWeekLoading,
    getWeeklyProgress,
    getAcceptedTrend
  } = useAnalytics();

  const { members, stats, isMembersLoading, isStatsLoading } = useTeam();

  // Fetch data for charts
  const {
    data: weeklyProgressData,
    isLoading: isWeeklyProgressLoading,
  } = getWeeklyProgress(weeks);

  const {
    data: acceptedTrendData,
    isLoading: isAcceptedTrendLoading,
  } = getAcceptedTrend(trendDays);

  // Prepare difficulty pie chart data
  const difficultyData = [
    { name: 'Easy', value: stats?.difficulty_breakdown?.easy || 0 },
    { name: 'Medium', value: stats?.difficulty_breakdown?.medium || 0 },
    { name: 'Hard', value: stats?.difficulty_breakdown?.hard || 0 },
  ];

  const handleDownloadExcel = () => {
    window.location.href = '/api/team/export/excel';
  };

  const handleCaptureScreenshot = async () => {
    if (chartsRef.current) {
      try {
        const canvas = await html2canvas(chartsRef.current, {
          backgroundColor: '#ffffff', // Ensure white background
          scale: 2, // Higher quality
        });

        const link = document.createElement('a');
        link.download = `analytics-dashboard-${new Date().toISOString().split('T')[0]}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
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
          <Button variant="outline" onClick={handleCaptureScreenshot}>
            <Camera className="mr-2 h-4 w-4" />
            Capture
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
          <CardTitle>Week-over-Week Changes</CardTitle>
          <CardDescription>
            Compare this week's progress to last week
          </CardDescription>
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
          data={acceptedTrendData || null}
          title="Daily Accepted Problems"
          description={`Daily submissions over the last ${trendDays} days`}
          isLoading={isAcceptedTrendLoading}
        />
      </div>

      {/* Team Performance & Difficulty Distribution */}
      <div className="grid gap-6 md:grid-cols-2">
        <TeamPerformanceChart
          members={members}
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
    </div>
  );
}
