import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Bell, AlertTriangle, Award, Calendar, X, RefreshCw } from 'lucide-react';
import { useNotifications, useClearNotifications, useCheckSubmissions } from '@/hooks/useNotifications';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';

export default function NotificationCenter() {
    const { data, isLoading } = useNotifications(20);
    const clearMutation = useClearNotifications();

    const checkSubmissionsMutation = useCheckSubmissions();

    const handleCheckSubmissions = () => {
        checkSubmissionsMutation.mutate(undefined, {
            onSuccess: (data) => {
                if (data.count > 0) {
                    toast.success(`Found ${data.count} new notification${data.count > 1 ? 's' : ''}!`, {
                        description: 'Check your notifications or Discord for details'
                    });
                } else {
                    toast.info('No new submissions found', {
                        description: 'You\'re all caught up!'
                    });
                }
            },
            onError: () => {
                toast.error('Failed to check submissions');
            }
        });
    };

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Bell className="h-5 w-5 text-primary" />
                        Notifications
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-16 bg-muted/30 rounded-lg animate-pulse" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    const notifications = data?.notifications || [];
    const unreadCount = data?.unread_count || 0;

    const getIcon = (type: string) => {
        switch (type) {
            case 'streak_at_risk':
                return <AlertTriangle className="h-4 w-4 text-orange-500" />;
            case 'milestone':
                return <Award className="h-4 w-4 text-green-500" />;
            case 'inactivity':
                return <Calendar className="h-4 w-4 text-blue-500" />;
            case 'daily_digest':
                return <Bell className="h-4 w-4 text-purple-500" />;
            case 'problem_solved':
                return <Award className="h-4 w-4 text-blue-500" />;
            default:
                return <Bell className="h-4 w-4 text-gray-500" />;
        }
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'high':
                return 'border-red-500/20 bg-red-500/5';
            case 'medium':
                return 'border-yellow-500/20 bg-yellow-500/5';
            default:
                return 'border-blue-500/20 bg-blue-500/5';
        }
    };

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Bell className="h-5 w-5 text-primary" />
                        <CardTitle>Notifications</CardTitle>
                        {unreadCount > 0 && (
                            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-primary text-primary-foreground">
                                {unreadCount}
                            </span>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Check Updates Button */}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleCheckSubmissions}
                            disabled={checkSubmissionsMutation.isPending}
                            title="Check for new submissions"
                        >
                            <RefreshCw className={`h-4 w-4 ${checkSubmissionsMutation.isPending ? 'animate-spin' : ''}`} />
                        </Button>

                        {notifications.length > 0 && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => clearMutation.mutate()}
                                disabled={clearMutation.isPending}
                            >
                                <X className="h-4 w-4 mr-1" />
                                Clear All
                            </Button>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {notifications.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                        No notifications yet. We'll notify you about streaks, milestones, and more!
                    </p>
                ) : (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                        {notifications.map((notification, index) => (
                            <div
                                key={index}
                                className={`p-3 rounded-lg border ${getPriorityColor(notification.priority)}`}
                            >
                                <div className="flex items-start gap-3">
                                    <div className="mt-0.5">{getIcon(notification.type)}</div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm">{notification.title}</p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {notification.message}
                                        </p>
                                        {notification.action && (
                                            <p className="text-xs text-primary mt-2">
                                                💡 {notification.action}
                                            </p>
                                        )}
                                        <p className="text-xs text-muted-foreground mt-2">
                                            {formatDistanceToNow(new Date(notification.created_at), {
                                                addSuffix: true,
                                            })}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
