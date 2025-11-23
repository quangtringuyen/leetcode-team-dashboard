import { useQuery } from '@tanstack/react-query';
import { leetcodeApi } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Circle, Clock, Trophy } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export default function DailyChallengeCompletions() {
    const { data, isLoading } = useQuery({
        queryKey: ['daily-completions'],
        queryFn: () => leetcodeApi.getDailyCompletions(),
        refetchInterval: 60000, // Refetch every minute
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
                <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm text-muted-foreground mb-3">
                        <span>Team Progress</span>
                        <span>
                            {completedCount} / {totalMembers} completed
                        </span>
                    </div>

                    <div className="space-y-2 max-h-[400px] overflow-y-auto">
                        {completions.map((member) => (
                            <div
                                key={member.username}
                                className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${member.completed
                                        ? 'bg-primary/5 border border-primary/20'
                                        : 'bg-muted/30'
                                    }`}
                            >
                                <Avatar className="h-9 w-9">
                                    <AvatarImage src={member.avatar || undefined} alt={member.name} />
                                    <AvatarFallback>{member.name.charAt(0).toUpperCase()}</AvatarFallback>
                                </Avatar>

                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">{member.name}</p>
                                    {member.completed && member.completionTime && (
                                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                                            <Clock className="h-3 w-3" />
                                            Completed at {member.completionTime}
                                        </p>
                                    )}
                                </div>

                                <div>
                                    {member.completed ? (
                                        <CheckCircle2 className="h-5 w-5 text-primary" />
                                    ) : (
                                        <Circle className="h-5 w-5 text-muted-foreground/30" />
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
