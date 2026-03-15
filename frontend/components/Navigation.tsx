'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, UserPlus, Camera, Video, FileImage, FileSpreadsheet } from 'lucide-react';

export default function Navigation() {
  const pathname = usePathname();

  // Self-register pages are student-facing — hide the nav bar
  if (pathname.startsWith('/self-register')) return null;

  const navItems = [
    { href: '/',             label: 'Dashboard',   icon: LayoutDashboard },
    { href: '/register',     label: 'Register',    icon: UserPlus },
    { href: '/bulk-import',  label: 'Bulk Import', icon: FileSpreadsheet },
    { href: '/attendance',   label: 'Attendance',  icon: Camera },
    { href: '/live',         label: 'Live',        icon: Video },
    { href: '/embeddings',   label: 'Embeddings',  icon: FileImage },
  ];

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
              <p className="text-xs text-gray-500">proxy kya hota hai?!</p>
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
        </div>
      </div>
    </nav>
  );
}
