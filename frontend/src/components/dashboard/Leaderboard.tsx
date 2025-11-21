import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { TeamMember } from '@/types';

interface LeaderboardProps {
  members: TeamMember[];
  isLoading?: boolean;
}

export default function Leaderboard({ members, isLoading }: LeaderboardProps) {
  if (isLoading) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle>Team Leaderboard</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-10 w-10 rounded-full" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-6 w-16" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle>Team Leaderboard</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {members.map((member, index) => {
            const rankChange = member.ranking || 0;
            const rankIcon =
              rankChange > 0 ? (
                <ArrowUp className="h-4 w-4 text-green-500" />
              ) : rankChange < 0 ? (
                <ArrowDown className="h-4 w-4 text-red-500" />
              ) : (
                <Minus className="h-4 w-4 text-muted-foreground" />
              );

            return (
              <div
                key={member.username}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent/50 transition-colors animate-slide-in"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {/* Rank */}
                <div className="flex items-center gap-2 w-12">
                  <span className="font-bold text-lg text-muted-foreground">
                    #{index + 1}
                  </span>
                </div>

                {/* Avatar */}
                <Avatar className="h-10 w-10">
                  <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                    {member.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>

                {/* Name & Username */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{member.name}</p>
                  <p className="text-sm text-muted-foreground truncate">
                    @{member.username}
                  </p>
                </div>

                {/* Rank Change */}
                <div className="flex items-center gap-1">
                  {rankIcon}
                  {rankChange !== 0 && (
                    <span className="text-xs text-muted-foreground">
                      {Math.abs(rankChange)}
                    </span>
                  )}
                </div>

                {/* Total Solved */}
                <Badge variant="secondary" className="font-semibold">
                  {member.totalSolved}
                </Badge>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
