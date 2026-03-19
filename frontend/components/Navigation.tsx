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
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-slate-900 flex items-center justify-center">
              <span className="text-white font-bold text-sm">H</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Here!</h1>
              <p className="text-xs text-gray-500">Face Recognition Attendance</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-slate-900 border-b-2 border-slate-900'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Icon size={18} />
                  <span className="hidden lg:inline">{item.label}</span>
                </Link>
              );
            })}
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated && user && (
              <>
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-gray-900">{user.username}</p>
                  <p className="text-xs text-gray-500 uppercase">{user.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-red-600 transition-colors"
                  title="Logout"
                >
                  <LogOut size={18} />
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
