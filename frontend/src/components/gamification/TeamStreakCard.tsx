import { Card, CardContent } from "@/components/ui/card";
import { Flame, Users } from "lucide-react";

interface TeamStreakCardProps {
    streak: number;
    activeToday: boolean;
    history?: string[];
    isLoading?: boolean;
}

const TeamStreakCard = ({ streak, activeToday, isLoading = false }: TeamStreakCardProps) => {

    if (isLoading) {
        return (
            <Card className="h-full bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950/20 dark:to-red-950/20 border-orange-200 dark:border-orange-800">
                <CardContent className="p-6 flex items-center justify-center">
                    <div className="animate-pulse flex flex-col items-center gap-2">
                        <div className="h-12 w-12 rounded-full bg-orange-200"></div>
                        <div className="h-6 w-24 bg-orange-200 rounded"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="h-full relative overflow-hidden bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950/20 dark:to-red-950/20 border-orange-200 dark:border-orange-800 shadow-sm transition-all hover:shadow-md">
            {/* Background Decorative Element */}
            <div className="absolute top-0 right-0 p-8 opacity-5">
                <Flame className="w-32 h-32" />
            </div>

            <CardContent className="p-6">
                <div className="flex flex-col items-center justify-center text-center space-y-2">

                    {/* Icon & Badge */}
                    <div className="relative mb-2">
                        <div className={`
                    w-16 h-16 rounded-full flex items-center justify-center
                    ${activeToday
                                ? 'bg-gradient-to-tr from-orange-500 to-red-600 shadow-lg shadow-orange-500/30'
                                : 'bg-muted text-muted-foreground'}
                `}>
                            <Flame className={`w-8 h-8 ${activeToday ? 'text-white fill-white animate-pulse' : ''}`} />
                        </div>
                        {activeToday && (
                            <div className="absolute -bottom-2 -right-2 bg-green-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full border-2 border-white dark:border-background">
                                ACTIVE
                            </div>
                        )}
                    </div>

                    {/* Streak Number */}
                    <div>
                        <div className="text-4xl font-black font-mono tracking-tight text-orange-600 dark:text-orange-500">
                            {streak}
                        </div>
                        <div className="text-sm font-semibold text-orange-600/80 dark:text-orange-400 uppercase tracking-widest">
                            Day Team Streak
                        </div>
                    </div>

                    {/* Helper Text */}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground bg-white/50 dark:bg-black/20 px-3 py-1.5 rounded-full mt-2">
                        <Users className="w-3 h-3" />
                        {activeToday
                            ? "Streak extended today! 🔥"
                            : "Someone needs to solve a problem today!"}
                    </div>

                </div>
            </CardContent>
        </Card>
    );
};

export default TeamStreakCard;
