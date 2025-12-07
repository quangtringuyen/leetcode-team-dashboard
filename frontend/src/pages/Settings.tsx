import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectItem } from '@/components/ui/select';
import { toast } from 'sonner';
import { Save, Settings as SettingsIcon, Clock, Bell } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Settings() {
    const queryClient = useQueryClient();
    const [weeklyGoal, setWeeklyGoal] = useState<string>('100');
    const [teamName, setTeamName] = useState<string>('LeetCode Team');
    const [snapshotDay, setSnapshotDay] = useState<string>('monday');
    const [snapshotTime, setSnapshotTime] = useState<string>('00:00');
    const [notificationInterval, setNotificationInterval] = useState<string>('15');
    const [problemsPerMember, setProblemsPerMember] = useState<string>('3');

    // Fetch settings
    const { data: settings, isLoading } = useQuery({
        queryKey: ['settings'],
        queryFn: async () => {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_URL}/settings`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            return response.data;
        }
    });

    // Update local state when settings load
    useEffect(() => {
        if (settings) {
            if (settings.weekly_goal) setWeeklyGoal(settings.weekly_goal.toString());
            if (settings.team_name) setTeamName(settings.team_name);
            if (settings.snapshot_schedule_day) setSnapshotDay(settings.snapshot_schedule_day);
            if (settings.snapshot_schedule_time) setSnapshotTime(settings.snapshot_schedule_time);
            if (settings.notification_check_interval) setNotificationInterval(settings.notification_check_interval.toString());
            if (settings.problems_per_member_weekly) setProblemsPerMember(settings.problems_per_member_weekly.toString());
        }
    }, [settings]);

    // Update setting mutation
    const updateSetting = useMutation({
        mutationFn: async ({ key, value }: { key: string; value: any }) => {
            const token = localStorage.getItem('token');
            await axios.post(`${API_URL}/settings`, { key, value }, {
                headers: { Authorization: `Bearer ${token}` }
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings'] });
            toast.success('Settings updated successfully');
        },
        onError: () => {
            toast.error('Failed to update settings');
        }
    });

    const handleSave = async () => {
        try {
            await updateSetting.mutateAsync({ key: 'weekly_goal', value: parseInt(weeklyGoal) });
            await updateSetting.mutateAsync({ key: 'team_name', value: teamName });
            await updateSetting.mutateAsync({ key: 'snapshot_schedule_day', value: snapshotDay });
            await updateSetting.mutateAsync({ key: 'snapshot_schedule_time', value: snapshotTime });
            await updateSetting.mutateAsync({ key: 'notification_check_interval', value: parseInt(notificationInterval) });
            await updateSetting.mutateAsync({ key: 'problems_per_member_weekly', value: parseInt(problemsPerMember) });
        } catch (error) {
            // Error handled in mutation
        }
    };

    if (isLoading) {
        return <div>Loading settings...</div>;
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold gradient-text flex items-center gap-2">
                    <SettingsIcon className="h-8 w-8" />
                    Settings
                </h1>
                <p className="text-muted-foreground mt-1">
                    Configure your team dashboard
                </p>
            </div>

            <Card className="glass">
                <CardHeader>
                    <CardTitle>General Settings</CardTitle>
                    <CardDescription>
                        Manage global settings for the dashboard
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="team-name">Team Name</Label>
                        <Input
                            id="team-name"
                            value={teamName}
                            onChange={(e) => setTeamName(e.target.value)}
                            placeholder="e.g. LeetCode Team"
                        />
                        <p className="text-xs text-muted-foreground">
                            Displayed in the browser tab and dashboard header.
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="weekly-goal">Weekly Problem Goal (Legacy)</Label>
                        <Input
                            id="weekly-goal"
                            type="number"
                            value={weeklyGoal}
                            onChange={(e) => setWeeklyGoal(e.target.value)}
                            placeholder="100"
                            disabled
                        />
                        <p className="text-xs text-muted-foreground">
                            This field is deprecated. Use "Problems Per Member Weekly" instead.
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="problems-per-member">Problems Per Member Weekly</Label>
                        <Input
                            id="problems-per-member"
                            type="number"
                            min="1"
                            max="50"
                            value={problemsPerMember}
                            onChange={(e) => setProblemsPerMember(e.target.value)}
                            placeholder="3"
                        />
                        <p className="text-xs text-muted-foreground">
                            Target number of problems each member should solve per week. Weekly goal = this × number of members.
                        </p>
                    </div>

                    <Button onClick={handleSave} disabled={updateSetting.isPending} className="mt-4">
                        <Save className="mr-2 h-4 w-4" />
                        {updateSetting.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                </CardContent>
            </Card>

            <Card className="glass">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Scheduler Settings
                    </CardTitle>
                    <CardDescription>
                        Configure automatic data collection and notifications
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                            <Label htmlFor="snapshot-day">Snapshot Day</Label>
                            <Select
                                id="snapshot-day"
                                value={snapshotDay}
                                onChange={(e) => setSnapshotDay(e.target.value)}
                            >
                                <SelectItem value="monday">Monday</SelectItem>
                                <SelectItem value="tuesday">Tuesday</SelectItem>
                                <SelectItem value="wednesday">Wednesday</SelectItem>
                                <SelectItem value="thursday">Thursday</SelectItem>
                                <SelectItem value="friday">Friday</SelectItem>
                                <SelectItem value="saturday">Saturday</SelectItem>
                                <SelectItem value="sunday">Sunday</SelectItem>
                            </Select>
                            <p className="text-xs text-muted-foreground">
                                Day of the week to automatically record team snapshots.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="snapshot-time">Snapshot Time</Label>
                            <Input
                                id="snapshot-time"
                                type="time"
                                value={snapshotTime}
                                onChange={(e) => setSnapshotTime(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">
                                Time of day to record snapshots (24-hour format).
                            </p>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="notification-interval" className="flex items-center gap-2">
                            <Bell className="h-4 w-4" />
                            Notification Check Interval (minutes)
                        </Label>
                        <Input
                            id="notification-interval"
                            type="number"
                            min="1"
                            max="1440"
                            value={notificationInterval}
                            onChange={(e) => setNotificationInterval(e.target.value)}
                            placeholder="15"
                        />
                        <p className="text-xs text-muted-foreground">
                            How often to check for new submissions and send Discord notifications (1-1440 minutes).
                        </p>
                    </div>

                    <Button onClick={handleSave} disabled={updateSetting.isPending} className="mt-4">
                        <Save className="mr-2 h-4 w-4" />
                        {updateSetting.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
