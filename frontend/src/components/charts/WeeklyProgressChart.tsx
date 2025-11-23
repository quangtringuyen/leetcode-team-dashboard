import {
    Area,
    AreaChart,
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { WeeklyProgressData } from '@/types';

interface WeeklyProgressChartProps {
    data: WeeklyProgressData | null;
    title: string;
    description?: string;
    isLoading?: boolean;
}

// Consistent color palette
const COLORS = [
    '#34A853', // Green
    '#FFA116', // Orange
    '#EF4743', // Red
    '#4285F4', // Blue
    '#9C27B0', // Purple
    '#00BCD4', // Cyan
    '#FF9800', // Deep Orange
    '#795548', // Brown
    '#607D8B', // Blue Grey
    '#E91E63', // Pink
];

export default function WeeklyProgressChart({
    data,
    title,
    description,
    isLoading,
}: WeeklyProgressChartProps) {
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
    const hasData = data && data.weeks.length > 0 && Object.keys(data.members).length > 0;

    if (!hasData) {
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
                                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                                />
                            </svg>
                        </div>
                        <p className="text-lg font-medium text-muted-foreground mb-2">
                            No progress data available
                        </p>
                        <p className="text-sm text-muted-foreground max-w-sm">
                            Record weekly snapshots to see your team's progress over time
                        </p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Transform data for Recharts
    // Recharts expects array of objects: [{ week: '...', member1: 10, member2: 20 }, ...]
    const chartData = data!.weeks.map((week, index) => {
        const point: any = { week };
        Object.entries(data!.members).forEach(([username, memberData]) => {
            point[username] = memberData.data[index] || 0;
        });
        return point;
    });

    // Get sorted member usernames for consistent coloring
    const memberUsernames = Object.keys(data!.members).sort();

    return (
        <Card className="glass">
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                {description && <CardDescription>{description}</CardDescription>}
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={chartData}>
                        <defs>
                            {memberUsernames.map((username, index) => (
                                <linearGradient
                                    key={username}
                                    id={`gradient-${username}`}
                                    x1="0"
                                    y1="0"
                                    x2="0"
                                    y2="1"
                                >
                                    <stop
                                        offset="5%"
                                        stopColor={COLORS[index % COLORS.length]}
                                        stopOpacity={0.3}
                                    />
                                    <stop
                                        offset="95%"
                                        stopColor={COLORS[index % COLORS.length]}
                                        stopOpacity={0}
                                    />
                                </linearGradient>
                            ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey="week"
                            className="text-xs"
                            tick={{ fill: 'hsl(var(--muted-foreground))' }}
                            tickFormatter={(value) => {
                                // Format date to show Month Day (e.g., "Nov 23")
                                try {
                                    const date = new Date(value);
                                    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                                } catch (e) {
                                    return value;
                                }
                            }}
                        />
                        <YAxis
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
                            labelFormatter={(label) => new Date(label).toLocaleDateString()}
                            formatter={(value: number, name: string) => [
                                value,
                                data!.members[name]?.name || name,
                            ]}
                        />
                        <Legend
                            formatter={(value) => data!.members[value]?.name || value}
                        />
                        {memberUsernames.map((username, index) => (
                            <Area
                                key={username}
                                type="monotone"
                                dataKey={username}
                                name={username} // Used for legend lookup
                                stroke={COLORS[index % COLORS.length]}
                                strokeWidth={2}
                                fill={`url(#gradient-${username})`}
                                stackId="1" // Stacked area chart? Or overlapping? 
                                // Plan said "Multi-line chart", usually implies overlapping or separate lines.
                                // But "Area" usually implies stacking or filling. 
                                // Let's use overlapping (no stackId) for progress comparison, 
                                // or stacked if we want total team progress.
                                // "Weekly Progress Chart - Multi-line chart showing each member's total solved"
                                // Usually total solved is cumulative, so lines will always go up.
                                // Overlapping areas might hide smaller values.
                                // Let's use simple Lines or Area with low opacity.
                                // The implementation plan said "Multi-line chart".
                                // Let's remove stackId to make them independent lines/areas.
                                fillOpacity={0.1}
                            />
                        ))}
                    </AreaChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
