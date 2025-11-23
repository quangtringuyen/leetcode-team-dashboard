import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Calendar, ExternalLink, CheckCircle2 } from 'lucide-react';
import { leetcodeApi } from '@/services/api';
import { DailyChallengeHistory } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';
import { format } from 'date-fns';

export default function RecentSubmissionsList() {
    const [history, setHistory] = useState<DailyChallengeHistory[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const data = await leetcodeApi.getDailyHistory(7);
                setHistory(data.history);
            } catch (error) {
                console.error('Failed to fetch daily challenge history:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchHistory();
    }, []);

    const getDifficultyColor = (difficulty: string) => {
        switch (difficulty.toLowerCase()) {
            case 'easy':
                return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'medium':
                return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
            case 'hard':
                return 'bg-red-500/20 text-red-400 border-red-500/30';
            default:
                return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
        }
    };

    if (isLoading) {
        return (
            <Card className="glass">
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-primary" />
                        Last 7 Days Challenges
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {[...Array(3)].map((_, i) => (
                            <div key={i} className="space-y-2">
                                <Skeleton className="h-4 w-3/4" />
                                <Skeleton className="h-3 w-1/2" />
                                <Skeleton className="h-6 w-full" />
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="glass">
            <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-primary" />
                    Last 7 Days Challenges
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                <ScrollArea className="h-[380px] px-6 pb-4">
                    <div className="space-y-4">
                        {history.length === 0 ? (
                            <div className="text-center text-muted-foreground py-8">
                                No daily challenge history available
                            </div>
                        ) : (
                            history.map((challenge, index) => (
                                <div
                                    key={`${challenge.date}-${challenge.titleSlug}`}
                                    className="pb-4 border-b border-border/50 last:border-0 last:pb-0 animate-slide-in"
                                    style={{ animationDelay: `${index * 50}ms` }}
                                >
                                    {/* Challenge Info */}
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs text-muted-foreground">
                                                    {format(new Date(challenge.date), 'MMM dd')}
                                                </span>
                                                <Badge
                                                    variant="outline"
                                                    className={`${getDifficultyColor(challenge.difficulty)} text-xs px-1.5 py-0`}
                                                >
                                                    {challenge.difficulty}
                                                </Badge>
                                            </div>
                                            <a
                                                href={challenge.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-sm font-medium hover:text-primary transition-colors flex items-center gap-1 w-fit group"
                                            >
                                                {challenge.title}
                                                <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </a>
                                        </div>
                                        <div className="text-xs text-muted-foreground flex items-center gap-1 whitespace-nowrap">
                                            <CheckCircle2 className="h-3 w-3" />
                                            {challenge.completedCount}/{challenge.totalMembers}
                                        </div>
                                    </div>

                                    {/* Completions */}
                                    {challenge.completions.length > 0 ? (
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {challenge.completions.map((completion) => (
                                                <div
                                                    key={`${challenge.date}-${completion.username}`}
                                                    className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-primary/10 border border-primary/20"
                                                >
                                                    <Avatar className="h-4 w-4 border border-primary/30">
                                                        <AvatarImage src={completion.avatar || undefined} alt={completion.name} />
                                                        <AvatarFallback className="text-[8px]">
                                                            {completion.name.charAt(0).toUpperCase()}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    <span className="text-xs font-medium">{completion.name}</span>
                                                    <span className="text-[10px] text-muted-foreground">
                                                        {completion.completionTime}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-xs text-muted-foreground italic mt-2">
                                            No completions
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
