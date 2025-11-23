import { Trophy, Medal } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { TeamMember } from '@/types';

interface PodiumProps {
  members: TeamMember[];
  isLoading?: boolean;
}

export default function Podium({ members, isLoading }: PodiumProps) {
  if (isLoading) {
    return (
      <Card className="glass p-6">
        <div className="flex items-end justify-center gap-4 h-64">
          <Skeleton className="h-40 w-32 rounded-lg" />
          <Skeleton className="h-52 w-32 rounded-lg" />
          <Skeleton className="h-36 w-32 rounded-lg" />
        </div>
      </Card>
    );
  }

  const topThree = members.slice(0, 3);
  const [second, first, third] = [topThree[1], topThree[0], topThree[2]].filter(Boolean);

  const PodiumPosition = ({
    member,
    position,
    height,
  }: {
    member: TeamMember;
    position: number;
    height: string;
  }) => {
    const colors = {
      1: 'from-yellow-500 to-yellow-600',
      2: 'from-slate-400 to-slate-500',
      3: 'from-amber-600 to-amber-700',
    };

    const icons = {
      1: <Trophy className="h-6 w-6 text-yellow-500" />,
      2: <Medal className="h-5 w-5 text-slate-400" />,
      3: <Medal className="h-5 w-5 text-amber-600" />,
    };

    return (
      <div className="flex flex-col items-center gap-3 animate-scale-in" style={{ animationDelay: `${position * 100}ms` }}>
        <div className="relative">
          {icons[position as keyof typeof icons]}
          <Avatar className="h-16 w-16 border-4 border-background shadow-lg mt-2">
            <AvatarFallback className={`bg-gradient-to-br ${colors[position as keyof typeof colors]} text-white text-xl font-bold`}>
              {member.name.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
        </div>
        <div className="text-center">
          <p className="font-semibold text-sm">{member.name}</p>
          <Badge variant="secondary" className="mt-1">
            {member.totalSolved} solved
          </Badge>
        </div>
        <div
          className={`w-32 rounded-t-lg bg-gradient-to-br ${colors[position as keyof typeof colors]} flex items-center justify-center text-white font-bold text-2xl shadow-lg`}
          style={{ height }}
        >
          {position}
        </div>
      </div>
    );
  };

  return (
    <Card className="glass p-6">
      <div className="flex flex-col items-center gap-8">
        <div className="text-center">
          <h3 className="text-2xl font-bold gradient-text">Top Performers</h3>
          <p className="text-muted-foreground text-sm mt-1">This week's champions</p>
        </div>

        <div className="flex items-end justify-center gap-4 h-64 mt-4">
          {second && <PodiumPosition member={second} position={2} height="10rem" />}
          {first && <PodiumPosition member={first} position={1} height="13rem" />}
          {third && <PodiumPosition member={third} position={3} height="9rem" />}
        </div>
      </div>
    </Card>
  );
}
