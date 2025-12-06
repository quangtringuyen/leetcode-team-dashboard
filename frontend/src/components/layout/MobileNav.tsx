import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MobileNav() {
    const location = useLocation();

    const navigation = [
        {
            name: 'Dashboard',
            path: '/',
            icon: LayoutDashboard,
        },
        {
            name: 'Analytics',
            path: '/analytics',
            icon: TrendingUp,
        },
        {
            name: 'Team',
            path: '/team',
            icon: Users,
        },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border/40 bg-background/95 backdrop-blur lg:hidden pb-safe">
            <nav className="flex justify-around items-center h-16 px-2">
                {navigation.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;

                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={cn(
                                'flex flex-col items-center justify-center w-full h-full gap-1 text-xs font-medium transition-colors',
                                isActive
                                    ? 'text-primary'
                                    : 'text-muted-foreground hover:text-foreground'
                            )}
                        >
                            <Icon className={cn("h-5 w-5", isActive && "fill-current")} />
                            <span>{item.name}</span>
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}
