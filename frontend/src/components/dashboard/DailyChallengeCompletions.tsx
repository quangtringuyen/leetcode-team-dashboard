import { useQuery } from '@tanstack/react-query';
import { leetcodeApi } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Clock, Trophy, Calendar } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function DailyChallengeCompletions() {
    const { data, isLoading } = useQuery({
        queryKey: ['daily-completions'],
        queryFn: () => leetcodeApi.getDailyCompletions(),
        refetchInterval: 60000, // Refetch every minute
    });

    const { data: historyData, isLoading: isHistoryLoading } = useQuery({
        queryKey: ['daily-history'],
        queryFn: () => leetcodeApi.getDailyHistory(),
        refetchInterval: 300000, // Refetch every 5 minutes
    });

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Today's Daily Challenge</CardTitle>
                    <CardDescription>Loading completion status...</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="flex items-center gap-3">
                                <Skeleton className="h-10 w-10 rounded-full" />
                                <div className="flex-1 space-y-2">
                                    <Skeleton className="h-4 w-32" />
                                    <Skeleton className="h-3 w-24" />
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!data) {
        return null;
    }

    const { challenge, completions, totalMembers, completedCount } = data;
    const completionRate = totalMembers > 0 ? Math.round((completedCount / totalMembers) * 100) : 0;

    return (
        <Card>
            <CardHeader>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <CardTitle className="text-lg">Today's Daily Challenge</CardTitle>
                        <CardDescription className="mt-1">
                            <a
                                href={challenge.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline font-medium"
                            >
                                {challenge.title}
                            </a>
                            <Badge
                                variant={
                                    challenge.difficulty === 'Easy'
                                        ? 'default'
                                        : challenge.difficulty === 'Medium'
                                            ? 'secondary'
                                            : 'destructive'
                                }
                                className="ml-2"
                            >
                                {challenge.difficulty}
                            </Badge>
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                        <Trophy className="h-4 w-4 text-primary" />
                        <span className="font-semibold">{completionRate}%</span>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <Tabs defaultValue="today" className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="today">
                            Today ({completedCount})
                        </TabsTrigger>
                        <TabsTrigger value="history">
                            <Calendar className="h-4 w-4 mr-2" />
                            Last 7 Days
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="today" className="mt-4">
                        <div className="space-y-1">
                            <div className="flex items-center justify-between text-sm text-muted-foreground mb-3">
                                <span>Completed Today</span>
                                <span>
                                    {completedCount} / {totalMembers} members
                                </span>
                            </div>

                            {completions.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    <Trophy className="h-12 w-12 mx-auto mb-2 opacity-20" />
                                    <p>No one has completed today's challenge yet!</p>
                                    <p className="text-sm mt-1">Be the first to solve it! 🚀</p>
                                </div>
                            ) : (
                                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 scrollbar-thin">
                                    {completions.map((member: any, index: number) => (
                                        <div
                                            key={member.username}
                                            className="flex items-center gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20 animate-slide-in"
                                            style={{ animationDelay: `${index * 50}ms` }}
                                        >
                                            <Avatar className="h-9 w-9">
                                                <AvatarImage src={member.avatar || undefined} alt={member.name} />
                                                <AvatarFallback>{member.name.charAt(0).toUpperCase()}</AvatarFallback>
                                            </Avatar>

                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{member.name}</p>
                                                {member.completionTime && (
                                                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                                                        <Clock className="h-3 w-3" />
                                                        Completed at {member.completionTime}
                                                    </p>
                                                )}
                                            </div>

                                            <div className="flex items-center gap-2">
                                                {index === 0 && <Trophy className="h-5 w-5 text-yellow-500" />}
                                                <CheckCircle2 className="h-5 w-5 text-primary" />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </TabsContent>

                    <TabsContent value="history" className="mt-4">
                        {isHistoryLoading ? (
                            <div className="space-y-3">
                                {[1, 2, 3].map((i) => (
                                    <Skeleton key={i} className="h-16 w-full" />
                                ))}
                            </div>
                        ) : historyData?.history && historyData.history.length > 0 ? (
                            <div className="space-y-2">
                                {historyData.history.map((day: any) => (
                                    <div
                                        key={day.date}
                                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <a
                                                href={day.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-sm font-medium hover:underline truncate block"
                                            >
                                                {day.title}
                                            </a>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="text-xs text-muted-foreground">{day.date}</span>
                                                <Badge
                                                    variant={
                                                        day.difficulty === 'Easy'
                                                            ? 'default'
                                                            : day.difficulty === 'Medium'
                                                                ? 'secondary'
                                                                : 'destructive'
                                                    }
                                                    className="text-xs"
                                                >
                                                    {day.difficulty}
                                                </Badge>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 ml-4">
                                            <div className="text-right">
                                                <p className="text-sm font-semibold">
                                                    {day.completedCount}/{day.totalMembers}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {Math.round((day.completedCount / day.totalMembers) * 100)}%
                                                </p>
                                            </div>
                                            <CheckCircle2
                                                className={`h-5 w-5 ${day.completedCount > 0 ? 'text-primary' : 'text-muted-foreground/30'
                                                    }`}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-muted-foreground">
                                <Calendar className="h-12 w-12 mx-auto mb-2 opacity-20" />
                                <p>No history available yet</p>
                            </div>
                        )}
                    </TabsContent>
                </Tabs>
            </CardContent>
        </Card>
    );
}
