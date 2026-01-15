import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Star } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export interface Achievement {
    key: string;
    name: string;
    description: string;
    icon: string;
    category: string;
    unlocked: boolean;
    unlocked_at?: string;
}

interface AchievementsPanelProps {
    achievements: Achievement[];
    isLoading?: boolean;
}

const AchievementsPanel = ({ achievements, isLoading = false }: AchievementsPanelProps) => {

    if (isLoading) {
        return (
            <Card className="border-none shadow-none bg-transparent">
                <CardHeader className="px-0 pb-2">
                    <CardTitle className="text-sm font-medium">Achievements</CardTitle>
                </CardHeader>
                <CardContent className="px-0">
                    <div className="flex gap-2 animate-pulse">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div key={i} className="h-10 w-10 bg-muted rounded-lg"></div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    const unlockedCount = achievements.filter(a => a.unlocked).length;
    const totalCount = achievements.length;

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardHeader className="px-0 pb-3 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    Achievements
                </CardTitle>
                <Badge variant="secondary" className="text-[10px] font-mono font-bold px-2 py-0">
                    {unlockedCount}/{totalCount}
                </Badge>
            </CardHeader>

            <CardContent className="px-0 pt-0">
                <div className="flex flex-wrap gap-2.5">
                    <TooltipProvider>
                        {achievements.map((achievement) => (
                            <Tooltip key={achievement.key}>
                                <TooltipTrigger asChild>
                                    <div
                                        className={`
                                            w-10 h-10 rounded-lg flex items-center justify-center text-lg border transition-all cursor-help
                                            ${achievement.unlocked
                                                ? 'bg-white dark:bg-zinc-900 border-yellow-200 dark:border-yellow-700/50 shadow-sm relative overflow-hidden'
                                                : 'bg-zinc-100 dark:bg-zinc-800 border-transparent grayscale opacity-30'}
                                        `}
                                    >
                                        {achievement.unlocked && (
                                            <div className="absolute top-0 right-0 w-2 h-2 bg-yellow-400 rounded-bl-sm opacity-50" />
                                        )}
                                        {achievement.icon}
                                    </div>
                                </TooltipTrigger>
                                <TooltipContent side="top">
                                    <div className="text-xs font-bold">{achievement.name}</div>
                                    <div className="text-[10px] text-muted-foreground">{achievement.description}</div>
                                </TooltipContent>
                            </Tooltip>
                        ))}
                    </TooltipProvider>
                </div>
            </CardContent>
        </Card>
    );
};

export default AchievementsPanel;
