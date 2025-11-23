import { useState } from 'react';
import { useAnalytics } from '@/hooks/useAnalytics';
import { useTeam } from '@/hooks/useTeam';
import TrendChart from '@/components/charts/TrendChart';
import DifficultyPieChart from '@/components/charts/DifficultyPieChart';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

export default function Analytics() {
  const [weeks, setWeeks] = useState(12);
  const { weekOverWeek, isWeekOverWeekLoading } = useAnalytics();
  const { getTrends } = useAnalytics();
  const { stats, isStatsLoading } = useTeam();

  const {
    data: trendsData,
    isLoading: isTrendsLoading,
  } = getTrends(weeks);

  // Prepare trend chart data
  const trendChartData = trendsData?.weeks?.map((week) => {
    const dataPoint: any = { week };
    Object.entries(trendsData?.members || {}).forEach(([member, data]) => {
      const weekData = data.find((d) => d.week === week);
      dataPoint[member] = weekData?.total || 0;
    });
    return dataPoint;
  }) || [];

  // Generate colors for trend lines
  const trendLines = Object.keys(trendsData?.members || {}).map((member, index) => ({
    key: member,
    name: member,
    color: `hsl(${(index * 360) / Object.keys(trendsData?.members || {}).length}, 70%, 50%)`,
  }));

  // Prepare difficulty pie chart data
  const difficultyData = [
    { name: 'Easy', value: stats?.difficulty_breakdown?.easy || 0 },
    { name: 'Medium', value: stats?.difficulty_breakdown?.medium || 0 },
    { name: 'Hard', value: stats?.difficulty_breakdown?.hard || 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold gradient-text">Analytics</h1>
        <p className="text-muted-foreground mt-1">
          Deep dive into your team's performance
        </p>
      </div>

      {/* Week Selector */}
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

      {/* Week-over-Week Changes */}
      <Card className="glass">
        <CardHeader>
          <CardTitle>Week-over-Week Changes</CardTitle>
          <CardDescription>
            Compare this week's progress to last week
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isWeekOverWeekLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : weekOverWeek.length === 0 ? (
            <p className="text-muted-foreground">No data available</p>
          ) : (
            <div className="space-y-3">
              {weekOverWeek.map((change) => {
                const changeIcon =
                  change.change > 0 ? (
                    <ArrowUp className="h-4 w-4 text-green-500" />
                  ) : change.change < 0 ? (
                    <ArrowDown className="h-4 w-4 text-red-500" />
                  ) : (
                    <Minus className="h-4 w-4 text-muted-foreground" />
                  );

                const changeColor =
                  change.change > 0
                    ? 'text-green-500'
                    : change.change < 0
                      ? 'text-red-500'
                      : 'text-muted-foreground';

                return (
                  <div
                    key={change.member}
                    className="flex items-center justify-between p-3 rounded-lg bg-accent/50"
                  >
                    <span className="font-medium">{change.member}</span>
                    <div className="flex items-center gap-4">
                      <div className="text-sm text-muted-foreground">
                        <span>Last: {change.lastWeek}</span>
                        <span className="mx-2">→</span>
                        <span>This: {change.thisWeek}</span>
                      </div>
                      <Badge variant="secondary" className={`gap-1 ${changeColor}`}>
                        {changeIcon}
                        {change.change > 0 ? '+' : ''}
                        {change.change}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trends Chart */}
      <TrendChart
        data={trendChartData}
        lines={trendLines}
        title="Problem Solving Trends"
        description={`Team progress over the last ${weeks} weeks`}
        isLoading={isTrendsLoading}
      />

      {/* Difficulty Distribution */}
      <DifficultyPieChart
        data={difficultyData}
        title="Difficulty Distribution"
        description="Breakdown of solved problems by difficulty"
        isLoading={isStatsLoading}
      />
    </div>
  );
}
