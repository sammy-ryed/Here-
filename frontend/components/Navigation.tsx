'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, UserPlus, Camera, FileImage, FileSpreadsheet, LogOut } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();

  // Self-register pages are student-facing — hide the nav bar
  if (pathname.startsWith('/self-register') || pathname === '/login') return null;

  const navItems = [
    { href: '/',             label: 'Dashboard',   icon: LayoutDashboard },
    { href: '/register',     label: 'Register',    icon: UserPlus },
    { href: '/bulk-import',  label: 'Bulk Import', icon: FileSpreadsheet },
    { href: '/attendance',   label: 'Attendance',  icon: Camera },
    { href: '/embeddings',   label: 'Embeddings',  icon: FileImage },
  ];

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16 gap-3 sm:gap-4">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-slate-900 flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-xs sm:text-sm">H</span>
            </div>
            <div className="hidden sm:block">
              <h1 className="text-base sm:text-lg font-semibold text-gray-900">Here!</h1>
              <p className="text-xs text-gray-500">Face Recognition Attendance</p>
            </div>
          </div>
          <div className="flex items-center gap-0.5 sm:gap-1 flex-1 sm:flex-initial justify-start sm:justify-center px-2 sm:px-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-1.5 px-2 sm:px-4 py-2 text-xs sm:text-sm font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-slate-900 border-b-2 border-slate-900'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title={item.label}
                >
                  <Icon size={16} className="sm:w-[18px] sm:h-[18px]" />
                  <span className="hidden lg:inline">{item.label}</span>
                </Link>
              );
            })}
          </div>
          <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
            {isAuthenticated && user && (
              <>
                <div className="text-right hidden sm:block">
                  <p className="text-xs sm:text-sm font-medium text-gray-900">{user.username}</p>
                  <p className="text-xs text-gray-500 uppercase">{user.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-2 sm:px-3 py-2 text-xs sm:text-sm font-medium text-gray-600 hover:text-red-600 transition-colors"
                  title="Logout"
                >
                  <LogOut size={16} className="sm:w-[18px] sm:h-[18px]" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
