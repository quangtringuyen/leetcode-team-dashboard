import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ArrowUp, ArrowDown } from "lucide-react";
import { WeekOverWeekChange } from "@/types";

interface WeekOverWeekTableProps {
    data: WeekOverWeekChange[];
    isLoading: boolean;
}

export default function WeekOverWeekTable({ data, isLoading }: WeekOverWeekTableProps) {
    if (isLoading) {
        return <div className="text-center p-4 text-muted-foreground">Loading...</div>;
    }

    if (!data || data.length === 0) {
        return <div className="text-center p-4 text-muted-foreground">No data available</div>;
    }

    return (
        <div className="rounded-md border">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[120px]">Week</TableHead>
                        <TableHead>Member</TableHead>
                        <TableHead className="text-right">Previous</TableHead>
                        <TableHead className="text-right">Current</TableHead>
                        <TableHead className="text-right">Change</TableHead>
                        <TableHead className="text-right">% Change</TableHead>
                        <TableHead className="text-right">Rank</TableHead>
                        <TableHead className="text-center">Rank Δ</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((row) => {
                        const isPositive = row.change > 0;
                        const isNegative = row.change < 0;

                        return (
                            <TableRow key={row.member}>
                                <TableCell className="font-medium">{row.week}</TableCell>
                                <TableCell>{row.member}</TableCell>
                                <TableCell className="text-right">{row.previous}</TableCell>
                                <TableCell className="text-right">{row.current}</TableCell>
                                <TableCell className="text-right">
                                    <div className="flex items-center justify-end gap-1">
                                        {isPositive ? (
                                            <div className="h-3 w-3 rounded-full bg-green-500" />
                                        ) : isNegative ? (
                                            <div className="h-3 w-3 rounded-full bg-red-500" />
                                        ) : (
                                            <div className="h-3 w-3 rounded-full bg-gray-400" />
                                        )}
                                        <span className={isPositive ? "text-green-600 font-bold" : isNegative ? "text-red-600 font-bold" : "text-muted-foreground"}>
                                            {isPositive ? "+" : ""}{row.change}
                                        </span>
                                    </div>
                                </TableCell>
                                <TableCell className="text-right">
                                    <span className={isPositive ? "text-green-600 font-bold" : isNegative ? "text-red-600 font-bold" : "text-muted-foreground"}>
                                        {isPositive ? "↗" : isNegative ? "↘" : ""} {row.pct_change}%
                                    </span>
                                </TableCell>
                                <TableCell className="text-right">{row.rank}</TableCell>
                                <TableCell className="text-center">
                                    {row.rank_delta > 0 ? (
                                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 gap-1">
                                            <ArrowUp className="h-3 w-3" /> {row.rank_delta}
                                        </Badge>
                                    ) : row.rank_delta < 0 ? (
                                        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 gap-1">
                                            <ArrowDown className="h-3 w-3" /> {Math.abs(row.rank_delta)}
                                        </Badge>
                                    ) : (
                                        <span className="text-muted-foreground text-xs">—</span>
                                    )}
                                </TableCell>
                            </TableRow>
                        );
                    })}
                </TableBody>
            </Table>
        </div>
    );
}
