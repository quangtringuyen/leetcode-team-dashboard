import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, Circle } from 'lucide-react';
import { useDifficultyTrends } from '@/hooks/useDifficultyTrends';

export default function DifficultyDistribution() {
    const { data: trends, isLoading } = useDifficultyTrends();

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        Difficulty Distribution
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-48 bg-muted/30 rounded-lg animate-pulse" />
                </CardContent>
            </Card>
        );
    }

    if (!trends || trends.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        Difficulty Distribution
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground text-center py-8">
                        No difficulty data available yet.
                    </p>
                </CardContent>
            </Card>
        );
    }


    const getStatusBadge = (status: string) => {
        if (status.includes('stuck')) return 'bg-red-500/10 text-red-700 dark:text-red-400';
        if (status.includes('progressing')) return 'bg-green-500/10 text-green-700 dark:text-green-400';
        if (status === 'advanced') return 'bg-purple-500/10 text-purple-700 dark:text-purple-400';
        return 'bg-blue-500/10 text-blue-700 dark:text-blue-400';
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Difficulty Distribution
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {trends.slice(0, 5).map((trend) => (
                        <div key={trend.member} className="space-y-2">
                            {/* Member Name and Status */}
                            <div className="flex items-center justify-between">
                                <span className="font-medium">{trend.name}</span>
                                <span className={`text-xs px-2 py-1 rounded-full ${getStatusBadge(trend.progression_status)}`}>
                                    {trend.progression_status.replace(/_/g, ' ')}
                                </span>
                            </div>

                            {/* Distribution Bars */}
                            <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                    <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                                        <div className="h-full flex">
                                            <div
                                                className="bg-green-500"
                                                style={{ width: `${trend.current_distribution.easy_pct}%` }}
                                            />
                                            <div
                                                className="bg-yellow-500"
                                                style={{ width: `${trend.current_distribution.medium_pct}%` }}
                                            />
                                            <div
                                                className="bg-red-500"
                                                style={{ width: `${trend.current_distribution.hard_pct}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Legend */}
                                <div className="flex items-center justify-between text-xs text-muted-foreground">
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-1">
                                            <Circle className="h-2 w-2 fill-green-500 text-green-500" />
                                            <span>Easy: {trend.current_distribution.easy}</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Circle className="h-2 w-2 fill-yellow-500 text-yellow-500" />
                                            <span>Medium: {trend.current_distribution.medium}</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <Circle className="h-2 w-2 fill-red-500 text-red-500" />
                                            <span>Hard: {trend.current_distribution.hard}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Recommendation */}
                            {trend.recommendation && (
                                <p className="text-xs text-muted-foreground italic">
                                    💡 {trend.recommendation}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
