import { Link, useLocation } from 'react-router-dom';
import { LogOut, Code2, Menu, Moon, Sun } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useState, useEffect } from 'react';

export default function Header() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const navigation = [
    { name: 'Dashboard', path: '/' },
    { name: 'Analytics', path: '/analytics' },
    { name: 'Team', path: '/team' },
    { name: 'Notifications', path: '/notifications' },
    { name: 'Settings', path: '/settings' },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <Code2 className="h-6 w-6 text-primary" />
          <span className="gradient-text">LeetCode Dashboard</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          {navigation.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`text-sm font-medium transition-colors hover:text-primary ${location.pathname === item.path
                ? 'text-foreground'
                : 'text-muted-foreground'
                }`}
            >
              {item.name}
            </Link>
          ))}
        </nav>

        {/* User menu */}
        <div className="flex items-center gap-4">
          {/* Dark Mode Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDarkMode(!darkMode)}
            className="gap-2"
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {darkMode ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>

          {/* Mobile Menu */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="sm">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64">
              <div className="flex flex-col gap-4 mt-8">
                <div className="flex items-center gap-3 pb-4 border-b">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <div className="text-sm">
                    <p className="font-medium">{user?.full_name || user?.username}</p>
                    <p className="text-muted-foreground text-xs">{user?.email}</p>
                  </div>
                </div>

                <nav className="flex flex-col gap-2">
                  {navigation.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent ${location.pathname === item.path
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                        }`}
                    >
                      {item.name}
                    </Link>
                  ))}
                </nav>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logout();
                  }}
                  className="gap-2 mt-4"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            </SheetContent>
          </Sheet>

          {/* Desktop User Info */}
          <div className="hidden md:flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary/10 text-primary">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="text-sm">
              <p className="font-medium">{user?.full_name || user?.username}</p>
              <p className="text-muted-foreground text-xs">{user?.email}</p>
            </div>
          </div>

          {/* Desktop Logout Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="gap-2 hidden md:flex"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
