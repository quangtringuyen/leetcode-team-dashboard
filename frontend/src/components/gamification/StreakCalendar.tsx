import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Flame, Trophy } from "lucide-react";
import { format, subDays, isSameDay, parseISO } from 'date-fns';

interface StreakCalendarProps {
    currentStreak: number;
    longestStreak: number;
    history?: string[];
    isLoading?: boolean;
}

const StreakCalendar = ({ currentStreak, longestStreak, history = [], isLoading = false }: StreakCalendarProps) => {
    // Generate last 14 days
    const days = Array.from({ length: 14 }, (_, i) => {
        const date = subDays(new Date(), 13 - i);
        return date;
    });

    if (isLoading) {
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Daily Streak</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="animate-pulse space-y-4">
                        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
                        <div className="h-4 bg-gray-200 rounded w-full"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Check if a date has activity
    const hasActivity = (date: Date) => {
        return history.some(h => isSameDay(parseISO(h), date));
    };

    // For demo if no history provided
    const dummyActivity = (date: Date) => {
        // Generate some fake activity for visual demo until API is fully implemented
        // In real implementation, remove this and use props.history
        const day = date.getDate();
        return day % 2 === 0 || day % 3 === 0;
    };

    const checkActivity = history.length > 0 ? hasActivity : dummyActivity;

    return (
        <Card className="h-full">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Flame className="h-5 w-5 text-orange-500 fill-orange-500" />
                        Daily Streak
                    </CardTitle>
                    <div className="text-2xl font-bold font-mono text-orange-500">
                        {currentStreak}
                        <span className="text-sm font-normal text-muted-foreground ml-1">days</span>
                    </div>
                </div>
            </CardHeader>

            <CardContent>
                {/* Streak Stats */}
                <div className="flex justify-between items-center mb-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                        <Trophy className="h-3 w-3" />
                        Longest: <span className="font-medium text-foreground">{longestStreak} days</span>
                    </div>
                    <div>
                        Last 14 Days
                    </div>
                </div>

                {/* Calendar Grid */}
                <div className="grid grid-cols-7 gap-2">
                    {days.map((date, i) => {
                        const isActive = checkActivity(date);
                        const isToday = isSameDay(date, new Date());

                        return (
                            <div key={i} className="flex flex-col items-center gap-1">
                                <div
                                    className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-all
                    ${isActive
                                            ? 'bg-orange-500 text-white shadow-sm ring-2 ring-orange-200 dark:ring-orange-900'
                                            : 'bg-muted text-muted-foreground hover:bg-muted/80'}
                    ${isToday ? 'ring-2 ring-offset-2 ring-primary' : ''}
                  `}
                                    title={format(date, 'MMM do, yyyy')}
                                >
                                    {format(date, 'd')}
                                </div>
                                <span className="text-[10px] text-muted-foreground">
                                    {format(date, 'EEEEE')}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </CardContent>
        </Card>
    );
};

export default StreakCalendar;
