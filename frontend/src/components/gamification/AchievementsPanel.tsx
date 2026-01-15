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

    // Dummy data if empty (for visual testing)
    const displayAchievements = achievements.length > 0 ? achievements : [
        { key: "1", name: "First Solve", description: "Solve your first problem", icon: "🌱", category: "starter", unlocked: true },
        { key: "2", name: "Streak Starter", description: "3 day streak", icon: "🔥", category: "streak", unlocked: true },
        { key: "3", name: "Week Warrior", description: "7 day streak", icon: "🔥🔥", category: "streak", unlocked: false },
        { key: "4", name: "Hard Mode", description: "Solve a Hard problem", icon: "💪", category: "difficulty", unlocked: false },
    ];

    if (isLoading) {
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Achievements</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-4 gap-4">
                        {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                            <div key={i} className="aspect-square bg-gray-200 rounded-lg animate-pulse"></div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Group achievements by category status
    const unlockedCount = displayAchievements.filter(a => a.unlocked).length;
    const totalCount = displayAchievements.length;
    const progressPercentage = Math.round((unlockedCount / totalCount) * 100) || 0;

    return (
        <Card className="h-full">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
                        Achievements
                    </CardTitle>
                    <Badge variant="secondary" className="font-mono">
                        {unlockedCount}/{totalCount}
                    </Badge>
                </div>
            </CardHeader>

            <CardContent>
                {/* Progress Bar */}
                <div className="w-full bg-secondary h-2 rounded-full mb-6 overflow-hidden">
                    <div
                        className="bg-yellow-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${progressPercentage}%` }}
                    ></div>
                </div>

                {/* Grid */}
                <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-3">
                    <TooltipProvider>
                        {displayAchievements.map((achievement) => (
                            <Tooltip key={achievement.key}>
                                <TooltipTrigger asChild>
                                    <div
                                        className={`
                      aspect-square rounded-xl flex items-center justify-center text-2xl border-2 transition-all cursor-help
                      ${achievement.unlocked
                                                ? 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200 shadow-sm dark:from-yellow-900/20 dark:to-orange-900/20 dark:border-yellow-700/50 grayscale-0'
                                                : 'bg-muted border-muted-foreground/20 grayscale opacity-50 hover:opacity-75'}
                    `}
                                    >
                                        {achievement.icon}
                                    </div>
                                </TooltipTrigger>
                                <TooltipContent side="bottom" className="max-w-[200px]">
                                    <div className="font-bold text-sm mb-1 flex items-center gap-2">
                                        {achievement.name}
                                        {achievement.unlocked && <span className="text-xs text-green-500">✓</span>}
                                    </div>
                                    <p className="text-xs text-muted-foreground">{achievement.description}</p>
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
