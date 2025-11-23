import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock, ExternalLink } from 'lucide-react';
import { leetcodeApi } from '@/services/api';
import { RecentSubmission } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDistanceToNow } from 'date-fns';

export default function RecentSubmissionsList() {
    const [submissions, setSubmissions] = useState<RecentSubmission[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchRecent = async () => {
            try {
                const data = await leetcodeApi.getRecentSubmissions(20);
                setSubmissions(data);
            } catch (error) {
                console.error('Failed to fetch recent submissions:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchRecent();
    }, []);

    if (isLoading) {
        return (
            <Card className="glass h-full">
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Clock className="h-5 w-5 text-primary" />
                        Recent Activity
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <Skeleton className="h-8 w-8 rounded-full" />
                                <div className="flex-1 space-y-1">
                                    <Skeleton className="h-4 w-3/4" />
                                    <Skeleton className="h-3 w-1/2" />
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="glass h-full">
            <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                    <Clock className="h-5 w-5 text-primary" />
                    Recent Activity
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                <ScrollArea className="h-[400px] px-6 pb-4">
                    <div className="space-y-4">
                        {submissions.length === 0 ? (
                            <div className="text-center text-muted-foreground py-8">
                                No recent activity found
                            </div>
                        ) : (
                            submissions.map((sub, index) => (
                                <div
                                    key={`${sub.username}-${sub.timestamp}-${index}`}
                                    className="flex items-start gap-3 pb-4 border-b border-border/50 last:border-0 last:pb-0 animate-slide-in"
                                    style={{ animationDelay: `${index * 50}ms` }}
                                >
                                    <Avatar className="h-8 w-8 mt-1">
                                        <AvatarFallback className="bg-primary/10 text-primary text-xs">
                                            {sub.name?.charAt(0).toUpperCase() || sub.username.charAt(0).toUpperCase()}
                                        </AvatarFallback>
                                    </Avatar>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex flex-col">
                                            <span className="font-medium text-sm">
                                                {sub.name || sub.username}
                                            </span>
                                            <a
                                                href={`https://leetcode.com/problems/${sub.titleSlug}/`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-sm text-muted-foreground hover:text-primary transition-colors truncate flex items-center gap-1 group"
                                            >
                                                {sub.title}
                                                <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </a>
                                        </div>
                                        <span className="text-xs text-muted-foreground mt-1 block">
                                            {formatDistanceToNow(new Date(parseInt(sub.timestamp) * 1000), { addSuffix: true })}
                                        </span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
