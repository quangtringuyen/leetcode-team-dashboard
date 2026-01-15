import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Award, Crown, Medal } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface LeaderboardEntry {
    rank: number;
    username: string;
    points: number;
    avatar?: string;
    isCurrentUser?: boolean;
}

interface GamificationLeaderboardProps {
    entries: LeaderboardEntry[];
    isLoading?: boolean;
}

const GamificationLeaderboard = ({ entries, isLoading = false }: GamificationLeaderboardProps) => {
    const [period, setPeriod] = useState("weekly");

    const getRankIcon = (rank: number) => {
        switch (rank) {
            case 1: return <Crown className="h-5 w-5 text-yellow-500 fill-yellow-500" />;
            case 2: return <Medal className="h-5 w-5 text-gray-400 fill-gray-400" />;
            case 3: return <Medal className="h-5 w-5 text-amber-700 fill-amber-700" />;
            default: return <span className="font-mono font-bold text-muted-foreground w-5 text-center">{rank}</span>;
        }
    };

    // Dummy data if empty (for visual testing)
    const displayEntries = entries.length > 0 ? entries : [
        { rank: 1, username: "Loading...", points: 0 },
        { rank: 2, username: "Loading...", points: 0 },
        { rank: 3, username: "Loading...", points: 0 },
    ];

    if (isLoading) {
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Leaderboard</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="flex items-center gap-4 animate-pulse">
                                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                                <div className="flex-1 h-4 bg-gray-200 rounded"></div>
                                <div className="w-12 h-4 bg-gray-200 rounded"></div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="h-full">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Award className="h-5 w-5 text-purple-500" />
                        Top Solvers
                    </CardTitle>
                    <Tabs value={period} className="w-[200px]" onValueChange={setPeriod}>
                        <TabsList className="grid w-full grid-cols-3 h-8">
                            <TabsTrigger value="weekly" className="text-xs px-1">Week</TabsTrigger>
                            <TabsTrigger value="monthly" className="text-xs px-1">Month</TabsTrigger>
                            <TabsTrigger value="all_time" className="text-xs px-1">Best</TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>
            </CardHeader>

            <CardContent className="px-2 sm:px-6">
                <div className="space-y-1">
                    {displayEntries.map((entry) => (
                        <div
                            key={entry.username}
                            className={`
                flex items-center justify-between p-2 rounded-lg transition-colors
                ${entry.isCurrentUser ? 'bg-primary/10 border border-primary/20' : 'hover:bg-muted/50'}
              `}
                        >
                            <div className="flex items-center gap-3">
                                <div className="flex items-center justify-center w-8">
                                    {getRankIcon(entry.rank)}
                                </div>

                                <div className="flex items-center gap-2">
                                    <Avatar className="h-8 w-8 border">
                                        <AvatarImage src={`https://github.com/${entry.username}.png`} />
                                        <AvatarFallback>{entry.username.substring(0, 2).toUpperCase()}</AvatarFallback>
                                    </Avatar>
                                    <span className={`font-medium ${entry.isCurrentUser ? 'text-primary' : ''}`}>
                                        {entry.username}
                                    </span>
                                </div>
                            </div>

                            <div className="font-mono font-bold text-sm">
                                {entry.points} <span className="text-xs font-normal text-muted-foreground">pts</span>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
};

export default GamificationLeaderboard;
