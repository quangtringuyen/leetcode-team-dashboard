import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Flame, Award } from 'lucide-react';
import { useStreakLeaderboard } from '@/hooks/useStreaks';

export default function StreakLeaderboard() {
    const { data: streaks, isLoading } = useStreakLeaderboard(5);

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Flame className="h-5 w-5 text-orange-500" />
                        Streak Leaderboard
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-16 bg-muted/30 rounded-lg animate-pulse" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!streaks || streaks.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Flame className="h-5 w-5 text-orange-500" />
                        Streak Leaderboard
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground text-center py-8">
                        No active streaks yet. Start solving to build your streak!
                    </p>
                </CardContent>
            </Card>
        );
    }

    const getStreakColor = (streak: number) => {
        if (streak >= 8) return 'text-orange-500';
        if (streak >= 4) return 'text-yellow-500';
        return 'text-blue-500';
    };

    const getStreakBg = (streak: number) => {
        if (streak >= 8) return 'bg-orange-500/10 border-orange-500/20';
        if (streak >= 4) return 'bg-yellow-500/10 border-yellow-500/20';
        return 'bg-blue-500/10 border-blue-500/20';
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Flame className="h-5 w-5 text-orange-500" />
                    Streak Leaderboard
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    {streaks.map((streak, index) => (
                        <div
                            key={streak.member}
                            className={`flex items-center gap-3 p-3 rounded-lg border transition-all hover:shadow-md ${getStreakBg(
                                streak.current_streak
                            )}`}
                        >
                            {/* Rank Badge */}
                            <div className="flex-shrink-0">
                                {index === 0 ? (
                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center">
                                        <Award className="h-4 w-4 text-white" />
                                    </div>
                                ) : (
                                    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                                        <span className="text-sm font-semibold text-muted-foreground">
                                            #{index + 1}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Member Info */}
                            <div className="flex-1 min-w-0">
                                <p className="font-medium truncate">{streak.name}</p>
                                <p className="text-xs text-muted-foreground">
                                    Longest: {streak.longest_streak} weeks
                                </p>
                            </div>

                            {/* Streak Count */}
                            <div className="flex items-center gap-2">
                                <Flame className={`h-5 w-5 ${getStreakColor(streak.current_streak)}`} />
                                <div className="text-right">
                                    <p className={`text-2xl font-bold ${getStreakColor(streak.current_streak)}`}>
                                        {streak.current_streak}
                                    </p>
                                    <p className="text-xs text-muted-foreground">weeks</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* View All Link */}
                {streaks.length >= 5 && (
                    <div className="mt-4 text-center">
                        <button className="text-sm text-primary hover:underline">
                            View All Streaks →
                        </button>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
