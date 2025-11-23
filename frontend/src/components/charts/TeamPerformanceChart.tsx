import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { TeamMember } from '@/types';

interface TeamPerformanceChartProps {
    members: TeamMember[];
    title: string;
    description?: string;
    isLoading?: boolean;
}

const COLORS = {
    Easy: '#34A853',   // Green
    Medium: '#FFA116', // Orange
    Hard: '#EF4743',   // Red
};

export default function TeamPerformanceChart({
    members,
    title,
    description,
    isLoading,
}: TeamPerformanceChartProps) {
    if (isLoading) {
        return (
            <Card className="glass">
                <CardHeader>
                    <CardTitle>{title}</CardTitle>
                    {description && <CardDescription>{description}</CardDescription>}
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-80 w-full" />
                </CardContent>
            </Card>
        );
    }

    // Check for empty data
    if (!members || members.length === 0) {
        return (
            <Card className="glass">
                <CardHeader>
                    <CardTitle>{title}</CardTitle>
                    {description && <CardDescription>{description}</CardDescription>}
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col items-center justify-center h-80 text-center">
                        <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center mb-4">
                            <svg
                                className="w-12 h-12 text-muted-foreground"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                                />
                            </svg>
                        </div>
                        <p className="text-lg font-medium text-muted-foreground mb-2">
                            No team members found
                        </p>
                        <p className="text-sm text-muted-foreground max-w-sm">
                            Add members to your team to see their performance comparison
                        </p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Transform data for Recharts
    // We need to extract Easy/Medium/Hard counts for each member
    // Note: The TeamMember type currently has 'totalSolved' but might not have breakdown
    // If breakdown is missing in TeamMember, we might need to fetch it or estimate it.
    // However, the backend /api/team/members endpoint usually returns full member data including stats.
    // Let's check the TeamMember type definition again.
    // Looking at types/index.ts:
    // export interface TeamMember {
    //   username: string;
    //   name: string;
    //   avatar?: string | null;
    //   totalSolved: number;
    //   ranking?: number | null;
    // }
    // It seems TeamMember doesn't have the breakdown!
    // But the backend `fetch_all_data` returns `user_data` which has `submissions` list.
    // And `api/team.py` -> `get_members` calls `fetch_all_data`.
    // So the response likely HAS the data, but our TypeScript interface is incomplete.
    // I should update the TypeScript interface first, but for now I'll cast or assume data exists.
    // Actually, looking at `backend/api/team.py`:
    // It returns `data` from `fetch_all_data`.
    // `fetch_all_data` returns list of user_data.
    // `user_data` from `fetch_user_data` has `submissions` list.
    // So we can calculate Easy/Medium/Hard from `submissions`.

    const chartData = members.map((member: any) => {
        let easy = 0, medium = 0, hard = 0;

        if (member.submissions) {
            member.submissions.forEach((sub: any) => {
                if (sub.difficulty === 'Easy') easy = parseInt(sub.count);
                if (sub.difficulty === 'Medium') medium = parseInt(sub.count);
                if (sub.difficulty === 'Hard') hard = parseInt(sub.count);
            });
        }

        return {
            name: member.name || member.username,
            Easy: easy,
            Medium: medium,
            Hard: hard,
            total: easy + medium + hard
        };
    }).sort((a, b) => b.total - a.total); // Sort by total solved descending

    return (
        <Card className="glass">
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                {description && <CardDescription>{description}</CardDescription>}
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={500}>
                    <BarChart
                        data={chartData}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" horizontal={false} />
                        <XAxis type="number" className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                        <YAxis
                            dataKey="name"
                            type="category"
                            width={100}
                            className="text-xs"
                            tick={{ fill: 'hsl(var(--muted-foreground))' }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--background))',
                                border: '1px solid hsl(var(--border))',
                                borderRadius: '8px',
                            }}
                            labelStyle={{ color: 'hsl(var(--foreground))' }}
                            cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                        />
                        <Legend />
                        <Bar dataKey="Easy" stackId="a" fill={COLORS.Easy} radius={[0, 0, 0, 0]} />
                        <Bar dataKey="Medium" stackId="a" fill={COLORS.Medium} radius={[0, 0, 0, 0]} />
                        <Bar dataKey="Hard" stackId="a" fill={COLORS.Hard} radius={[0, 4, 4, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
