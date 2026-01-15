import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Trophy, Crown, Medal } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface UnifiedLeaderboardProps {
    problemSolvers: any[];
    pointEarners: any[];
    isLoading?: boolean;
}

const UnifiedLeaderboard = ({ problemSolvers, pointEarners, isLoading = false }: UnifiedLeaderboardProps) => {
    const [activeTab, setActiveTab] = useState("problems");

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

    const getRankIcon = (rank: number) => {
        switch (rank) {
            case 1: return <Crown className="h-5 w-5 text-yellow-500 fill-yellow-500" />;
            case 2: return <Medal className="h-5 w-5 text-gray-400 fill-gray-400" />;
            case 3: return <Medal className="h-5 w-5 text-amber-700 fill-amber-700" />;
            default: return <span className="font-mono font-bold text-muted-foreground w-5 text-center">{rank}</span>;
        }
    };

    const renderList = (data: any[], type: 'problems' | 'points') => (
        <div className="space-y-1">
            {data.map((entry, index) => {
                const rank = index + 1;
                const value = type === 'problems' ? entry.totalSolved : entry.points;
                const label = type === 'problems' ? 'solved' : 'pts';

                return (
                    <div
                        key={entry.username}
                        className={`
              flex items-center justify-between p-2 rounded-lg transition-colors
              ${entry.isCurrentUser ? 'bg-primary/10 border border-primary/20' : 'hover:bg-muted/50'}
            `}
                    >
                        <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center w-8">
                                {getRankIcon(rank)}
                            </div>

                            <div className="flex items-center gap-2">
                                <Avatar className="h-7 w-7 border">
                                    <AvatarImage src={entry.avatar_url || `https://github.com/${entry.username}.png`} />
                                    <AvatarFallback>{entry.username.substring(0, 2).toUpperCase()}</AvatarFallback>
                                </Avatar>
                                <span className={`font-medium text-sm ${entry.isCurrentUser ? 'text-primary' : ''}`}>
                                    {entry.name || entry.username}
                                </span>
                            </div>
                        </div>

                        <div className="font-mono font-bold text-sm">
                            {value} <span className="text-xs font-normal text-muted-foreground">{label}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );

    return (
        <Card className="h-full">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Trophy className="h-5 w-5 text-primary" />
                        Rankings
                    </CardTitle>
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-[200px]">
                        <TabsList className="grid w-full grid-cols-2 h-8">
                            <TabsTrigger value="problems" className="text-xs">Problems</TabsTrigger>
                            <TabsTrigger value="points" className="text-xs">Points</TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>
            </CardHeader>

            <CardContent className="px-2 sm:px-6">
                {activeTab === 'problems' && renderList(problemSolvers.slice(0, 10), 'problems')}
                {activeTab === 'points' && renderList(pointEarners || [], 'points')}
            </CardContent>
        </Card>
    );
};

export default UnifiedLeaderboard;
