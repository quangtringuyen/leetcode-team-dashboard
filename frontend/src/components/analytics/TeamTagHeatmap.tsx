import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Hash, TrendingUp, AlertCircle } from 'lucide-react';
import { useTeamHeatmap } from '@/hooks/useTagAnalysis';

export default function TeamTagHeatmap() {
    const { data: heatmap, isLoading } = useTeamHeatmap(50);

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Hash className="h-5 w-5 text-primary" />
                        Team Topic Coverage
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="h-32 bg-muted/30 rounded-lg animate-pulse" />
                        <div className="h-32 bg-muted/30 rounded-lg animate-pulse" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!heatmap) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Hash className="h-5 w-5 text-primary" />
                        Team Topic Coverage
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground text-center py-8">
                        No tag data available yet.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Hash className="h-5 w-5 text-primary" />
                    Team Topic Coverage
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Coverage Score */}
                <div className="flex items-center justify-between p-4 rounded-lg bg-primary/5 border border-primary/10">
                    <div>
                        <p className="text-sm text-muted-foreground">Coverage Score</p>
                        <p className="text-2xl font-bold text-primary">
                            {heatmap.team_coverage_score}%
                        </p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-muted-foreground">Unique Topics</p>
                        <p className="text-2xl font-bold">{heatmap.total_unique_tags}</p>
                    </div>
                </div>

                {/* Team Strengths */}
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <TrendingUp className="h-4 w-4 text-green-500" />
                        <h3 className="font-semibold text-sm">Team Strengths</h3>
                    </div>
                    <div className="space-y-2">
                        {heatmap.team_strengths.slice(0, 5).map((strength) => (
                            <div
                                key={strength.tag}
                                className="flex items-center justify-between p-2 rounded-md bg-green-500/5 border border-green-500/10"
                            >
                                <span className="text-sm font-medium">{strength.tag}</span>
                                <div className="flex items-center gap-2">
                                    <div className="w-24 bg-muted rounded-full h-1.5 overflow-hidden">
                                        <div
                                            className="h-full bg-green-500"
                                            style={{ width: `${Math.min(strength.percentage, 100)}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-muted-foreground w-12 text-right">
                                        {strength.count} problems
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Team Weaknesses */}
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <AlertCircle className="h-4 w-4 text-orange-500" />
                        <h3 className="font-semibold text-sm">Areas to Improve</h3>
                    </div>
                    <div className="space-y-2">
                        {heatmap.team_weaknesses.slice(0, 5).map((weakness) => (
                            <div
                                key={weakness.tag}
                                className="flex items-center justify-between p-2 rounded-md bg-orange-500/5 border border-orange-500/10"
                            >
                                <div className="flex-1">
                                    <p className="text-sm font-medium">{weakness.tag}</p>
                                    <p className="text-xs text-muted-foreground">
                                        {weakness.recommendation}
                                    </p>
                                </div>
                                <span className="text-xs text-orange-600 dark:text-orange-400 font-medium">
                                    {weakness.count} solved
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
