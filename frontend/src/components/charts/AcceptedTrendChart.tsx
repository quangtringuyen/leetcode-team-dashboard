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
import { AcceptedTrendData } from '@/types';

interface AcceptedTrendChartProps {
    data: AcceptedTrendData[] | null;
    title: string;
    description?: string;
    isLoading?: boolean;
}

// Consistent color palette (same as WeeklyProgressChart)
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

export default function AcceptedTrendChart({
    data,
    title,
    description,
    isLoading,
}: AcceptedTrendChartProps) {
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
    const hasData = data && data.length > 0;

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
                                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                                />
                            </svg>
                        </div>
                        <p className="text-lg font-medium text-muted-foreground mb-2">
                            No trend data available
                        </p>
                        <p className="text-sm text-muted-foreground max-w-sm">
                            Daily submission data will appear here once your team starts solving problems
                        </p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Transform data for Recharts Stacked Bar Chart
    // Input: [{ date: '2023-01-01', member: 'Alice', accepted: 5 }, ...]
    // Output: [{ date: '2023-01-01', Alice: 5, Bob: 0 }, ...]

    const chartDataMap = new Map<string, any>();
    const membersSet = new Set<string>();

    data!.forEach((item) => {
        const date = item.date;
        membersSet.add(item.member);

        if (!chartDataMap.has(date)) {
            chartDataMap.set(date, { date });
        }

        const entry = chartDataMap.get(date);
        entry[item.member] = (entry[item.member] || 0) + item.accepted;
    });

    const chartData = Array.from(chartDataMap.values()).sort((a, b) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const members = Array.from(membersSet).sort();

    return (
        <Card className="glass">
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                {description && <CardDescription>{description}</CardDescription>}
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey="date"
                            className="text-xs"
                            tick={{ fill: 'hsl(var(--muted-foreground))' }}
                            tickFormatter={(value) => {
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
                            cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                        />
                        <Legend />
                        {members.map((member, index) => (
                            <Bar
                                key={member}
                                dataKey={member}
                                stackId="a"
                                fill={COLORS[index % COLORS.length]}
                                radius={[4, 4, 0, 0]}
                            />
                        ))}
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
