import { useState } from "react";
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
    const [sortKey, setSortKey] = useState<keyof WeekOverWeekChange>('week');
    const [sortAsc, setSortAsc] = useState<boolean>(false);

    const toggleSort = (key: keyof WeekOverWeekChange) => {
        if (key === sortKey) {
            setSortAsc(!sortAsc);
        } else {
            setSortKey(key);
            setSortAsc(true);
        }
    };

    const sortedData = [...data].sort((a, b) => {
        const aVal = a[sortKey];
        const bVal = b[sortKey];
        if (aVal < bVal) return sortAsc ? -1 : 1;
        if (aVal > bVal) return sortAsc ? 1 : -1;
        return 0;
    });

    if (isLoading) {
        return <div className="text-center p-4 text-muted-foreground">Loading...</div>;
    }

    if (!data || data.length === 0) {
        return <div className="text-center p-4 text-muted-foreground">No data available</div>;
    }

    return (
        <div className="rounded-md border overflow-x-auto">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[120px] cursor-pointer" onClick={() => toggleSort('week')}>Week {sortKey === 'week' && (sortAsc ? '▲' : '▼')}</TableHead>
                        <TableHead className="cursor-pointer" onClick={() => toggleSort('member')}>Member {sortKey === 'member' && (sortAsc ? '▲' : '▼')}</TableHead>
                        <TableHead className="text-right cursor-pointer" onClick={() => toggleSort('previous')}>Previous {sortKey === 'previous' && (sortAsc ? '▲' : '▼')}</TableHead>
                        <TableHead className="text-right cursor-pointer" onClick={() => toggleSort('current')}>Current {sortKey === 'current' && (sortAsc ? '▲' : '▼')}</TableHead>
                        <TableHead className="text-right cursor-pointer" onClick={() => toggleSort('change')}>Change {sortKey === 'change' && (sortAsc ? '▲' : '▼')}</TableHead>
                        <TableHead className="text-right cursor-pointer" onClick={() => toggleSort('pct_change')}>% Change {sortKey === 'pct_change' && (sortAsc ? '▲' : '▼')}</TableHead>
                        <TableHead className="text-right cursor-pointer" onClick={() => toggleSort('rank')}>Rank {sortKey === 'rank' && (sortAsc ? '▲' : '▼')}</TableHead>
                        <TableHead className="text-center cursor-pointer" onClick={() => toggleSort('rank_delta')}>Rank Δ {sortKey === 'rank_delta' && (sortAsc ? '▲' : '▼')}</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {sortedData.map((row) => {
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
