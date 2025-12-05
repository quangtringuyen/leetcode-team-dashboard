import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, Clock } from 'lucide-react';
import { useStreaksAtRisk } from '@/hooks/useStreaks';

export default function StreakAtRiskAlert() {
    const { data: atRiskMembers, isLoading } = useStreaksAtRisk();

    if (isLoading || !atRiskMembers || atRiskMembers.length === 0) {
        return null;
    }

    return (
        <Card className="border-orange-200 bg-orange-50/50 dark:bg-orange-950/20 dark:border-orange-900/50">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-700 dark:text-orange-400">
                    <AlertTriangle className="h-5 w-5" />
                    Streaks at Risk
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-orange-600 dark:text-orange-300 mb-3">
                    {atRiskMembers.length} {atRiskMembers.length === 1 ? 'member' : 'members'} haven't
                    solved problems recently. Their streaks are about to break!
                </p>
                <div className="space-y-2">
                    {atRiskMembers.map((member) => (
                        <div
                            key={member.member}
                            className="flex items-center justify-between p-2 rounded-md bg-white/50 dark:bg-black/20"
                        >
                            <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 text-orange-500" />
                                <span className="font-medium text-sm">{member.name}</span>
                            </div>
                            <span className="text-xs text-muted-foreground">
                                Last active: {member.last_active_date}
                            </span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
