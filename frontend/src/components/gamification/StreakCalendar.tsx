import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Flame, Trophy } from "lucide-react";
import { format, subDays, isSameDay, parseISO } from 'date-fns';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface StreakCalendarProps {
    currentStreak: number;
    longestStreak: number;
    history?: string[];
    isLoading?: boolean;
}

const StreakCalendar = ({ currentStreak, longestStreak, history = [], isLoading = false }: StreakCalendarProps) => {
    // Generate last 28 days (4 weeks) for a better "heatmap" look
    const days = Array.from({ length: 28 }, (_, i) => {
        const date = subDays(new Date(), 27 - i);
        return date;
    });

    if (isLoading) {
        return (
            <Card className="border shadow-sm">
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Activity Heatmap</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-7 gap-1.5 animate-pulse">
                        {Array.from({ length: 14 }).map((_, i) => (
                            <div key={i} className="aspect-square bg-muted rounded-sm"></div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    const hasActivity = (date: Date) => {
        return history.some(h => isSameDay(parseISO(h), date));
    };

    return (
        <Card className="border shadow-sm overflow-hidden">
            <CardHeader className="pb-4 bg-zinc-50/50 dark:bg-zinc-900/50 border-b">
                <div className="flex justify-between items-center">
                    <div className="space-y-1">
                        <CardTitle className="text-sm font-bold flex items-center gap-2">
                            <Flame className="h-4 w-4 text-orange-500 fill-orange-500" />
                            Activity Streak
                        </CardTitle>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
                            Last 28 Days
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-black text-orange-600 dark:text-orange-500 leading-none">
                            {currentStreak}
                        </div>
                        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-tighter">
                            Days
                        </div>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="pt-5 flex flex-col gap-4">
                {/* Heatmap Grid */}
                <div className="grid grid-cols-7 gap-1.5 self-center">
                    <TooltipProvider>
                        {days.map((date, i) => {
                            const isActive = hasActivity(date);
                            const isToday = isSameDay(date, new Date());

                            return (
                                <Tooltip key={i}>
                                    <TooltipTrigger asChild>
                                        <div
                                            className={`
                                                w-7 h-7 rounded-sm transition-all duration-300
                                                ${isActive
                                                    ? 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.3)]'
                                                    : 'bg-zinc-100 dark:bg-zinc-800'}
                                                ${isToday ? 'ring-2 ring-zinc-900 dark:ring-zinc-100 ring-offset-2 dark:ring-offset-zinc-950' : ''}
                                                hover:scale-110 cursor-pointer
                                            `}
                                        />
                                    </TooltipTrigger>
                                    <TooltipContent side="top">
                                        <div className="text-[10px] font-bold">
                                            {format(date, 'MMM d, yyyy')}
                                        </div>
                                        <div className="text-[10px] text-muted-foreground">
                                            {isActive ? 'Activity recorded' : 'No activity'}
                                        </div>
                                    </TooltipContent>
                                </Tooltip>
                            );
                        })}
                    </TooltipProvider>
                </div>

                {/* Legend & Stats */}
                <div className="flex justify-between items-center pt-2 border-t border-zinc-50 dark:border-zinc-900 mt-1">
                    <div className="flex items-center gap-2 text-[11px] font-medium text-muted-foreground">
                        <Trophy className="h-3 w-3 text-yellow-500" />
                        <span>Best: {longestStreak}d</span>
                    </div>
                    <div className="flex items-center gap-1 text-[9px] text-muted-foreground font-bold uppercase tracking-widest opacity-60">
                        <span>Less</span>
                        <div className="w-2 h-2 rounded-sm bg-zinc-100 dark:bg-zinc-800" />
                        <div className="w-2 h-2 rounded-sm bg-orange-500" />
                        <span>More</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default StreakCalendar;
