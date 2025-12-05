import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tag, Award, AlertTriangle } from 'lucide-react';
import { useTagAnalysis } from '@/hooks/useTagAnalysis';

export default function MemberTagCoverage() {
    const { data: analysis, isLoading } = useTagAnalysis(50);

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Tag className="h-5 w-5 text-primary" />
                        Topic Coverage by Member
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-24 bg-muted/30 rounded-lg animate-pulse" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!analysis || analysis.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Tag className="h-5 w-5 text-primary" />
                        Topic Coverage by Member
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground text-center py-8">
                        No tag data available. This may take a while to load...
                    </p>
                </CardContent>
            </Card>
        );
    }

    const getCoverageColor = (score: number) => {
        if (score >= 60) return 'text-green-600 dark:text-green-400';
        if (score >= 40) return 'text-yellow-600 dark:text-yellow-400';
        return 'text-orange-600 dark:text-orange-400';
    };

    const getCoverageBg = (score: number) => {
        if (score >= 60) return 'bg-green-500/10 border-green-500/20';
        if (score >= 40) return 'bg-yellow-500/10 border-yellow-500/20';
        return 'bg-orange-500/10 border-orange-500/20';
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Tag className="h-5 w-5 text-primary" />
                    Topic Coverage by Member
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {analysis.slice(0, 5).map((member) => (
                        <div
                            key={member.member}
                            className={`p-4 rounded-lg border ${getCoverageBg(member.coverage_score)}`}
                        >
                            {/* Member Header */}
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <p className="font-semibold">{member.name}</p>
                                    <p className="text-xs text-muted-foreground">
                                        {member.total_unique_tags} topics covered
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className={`text-2xl font-bold ${getCoverageColor(member.coverage_score)}`}>
                                        {member.coverage_score}%
                                    </p>
                                    <p className="text-xs text-muted-foreground">coverage</p>
                                </div>
                            </div>

                            {/* Top Tags */}
                            {member.top_tags.length > 0 && (
                                <div className="mb-3">
                                    <div className="flex items-center gap-1 mb-2">
                                        <Award className="h-3 w-3 text-green-500" />
                                        <span className="text-xs font-medium text-muted-foreground">
                                            Top Topics
                                        </span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {member.top_tags.slice(0, 5).map((tag) => (
                                            <span
                                                key={tag.tag}
                                                className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-700 dark:text-green-400"
                                            >
                                                {tag.tag} ({tag.count})
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Weak Tags */}
                            {member.weak_tags.length > 0 && (
                                <div>
                                    <div className="flex items-center gap-1 mb-2">
                                        <AlertTriangle className="h-3 w-3 text-orange-500" />
                                        <span className="text-xs font-medium text-muted-foreground">
                                            Needs Practice
                                        </span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {member.weak_tags.slice(0, 3).map((tag) => (
                                            <span
                                                key={tag.tag}
                                                className="text-xs px-2 py-1 rounded-full bg-orange-500/10 text-orange-700 dark:text-orange-400"
                                            >
                                                {tag.tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Recommendation */}
                            {member.recommendation && (
                                <p className="text-xs text-muted-foreground italic mt-3 pt-3 border-t">
                                    💡 {member.recommendation}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
