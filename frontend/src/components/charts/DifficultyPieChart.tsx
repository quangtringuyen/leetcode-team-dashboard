import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface DifficultyPieChartProps {
  data: {
    name: string;
    value: number;
  }[];
  title: string;
  description?: string;
  isLoading?: boolean;
}

const COLORS = {
  Easy: '#10b981', // green-500
  Medium: '#f59e0b', // amber-500
  Hard: '#ef4444', // red-500
};

export default function DifficultyPieChart({
  data,
  title,
  description,
  isLoading,
}: DifficultyPieChartProps) {
  if (isLoading) {
    return (
      <Card className="glass">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <Skeleton className="h-80 w-full rounded-full" />
        </CardContent>
      </Card>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);

  const CustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="font-semibold text-sm"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={CustomLabel}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[entry.name as keyof typeof COLORS]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>

        {/* Summary */}
        <div className="mt-6 grid grid-cols-3 gap-4 text-center">
          {data.map((item) => (
            <div key={item.name} className="space-y-1">
              <div
                className="w-3 h-3 rounded-full mx-auto"
                style={{ backgroundColor: COLORS[item.name as keyof typeof COLORS] }}
              />
              <p className="text-sm font-medium">{item.name}</p>
              <p className="text-2xl font-bold">{item.value}</p>
              <p className="text-xs text-muted-foreground">
                {((item.value / total) * 100).toFixed(1)}%
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
