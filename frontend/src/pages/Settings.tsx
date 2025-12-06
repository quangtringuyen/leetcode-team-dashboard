import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Save, Settings as SettingsIcon } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export default function Settings() {
    const queryClient = useQueryClient();
    const [weeklyGoal, setWeeklyGoal] = useState<string>('100');
    const [teamName, setTeamName] = useState<string>('LeetCode Team');

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
                        <Label htmlFor="weekly-goal">Weekly Problem Goal</Label>
                        <Input
                            id="weekly-goal"
                            type="number"
                            value={weeklyGoal}
                            onChange={(e) => setWeeklyGoal(e.target.value)}
                            placeholder="100"
                        />
                        <p className="text-xs text-muted-foreground">
                            The target number of problems for the team to solve collectively each week.
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
