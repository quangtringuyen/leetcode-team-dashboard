import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, ExternalLink } from 'lucide-react';
import { leetcodeApi } from '@/services/api';
import { DailyChallenge } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';

export default function DailyChallengeCard() {
    const [challenge, setChallenge] = useState<DailyChallenge | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchDaily = async () => {
            try {
                const data = await leetcodeApi.getDailyChallenge();
                setChallenge(data);
            } catch (error) {
                console.error('Failed to fetch daily challenge:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchDaily();
    }, []);

    if (isLoading) {
        return (
            <Card className="glass">
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-primary" />
                        Daily Challenge
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        <Skeleton className="h-6 w-3/4" />
                        <div className="flex gap-2">
                            <Skeleton className="h-5 w-16" />
                            <Skeleton className="h-5 w-24" />
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!challenge) {
        return null;
    }

    const difficultyColor =
        challenge.difficulty === 'Easy' ? 'bg-green-500/10 text-green-500 hover:bg-green-500/20' :
            challenge.difficulty === 'Medium' ? 'bg-orange-500/10 text-orange-500 hover:bg-orange-500/20' :
                'bg-red-500/10 text-red-500 hover:bg-red-500/20';

    return (
        <Card className="glass hover:border-primary/50 transition-colors">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-primary" />
                    Daily Challenge
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div>
                        <h3 className="font-semibold text-lg line-clamp-1" title={challenge.title}>
                            {challenge.title}
                        </h3>
                        <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className={difficultyColor}>
                                {challenge.difficulty}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                                {new Date(challenge.date).toLocaleDateString(undefined, {
                                    weekday: 'long',
                                    month: 'short',
                                    day: 'numeric'
                                })}
                            </span>
                        </div>
                    </div>

                    <Button
                        className="w-full gap-2"
                        onClick={() => window.open(`https://leetcode.com${challenge.link}`, '_blank')}
                    >
                        Solve Now
                        <ExternalLink className="h-4 w-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
