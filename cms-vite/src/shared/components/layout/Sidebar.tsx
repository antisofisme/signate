/**
 * Sidebar Component
 *
 * LAYER 1: PRESENTATION
 * Main navigation sidebar
 */

import { Link, useLocation } from 'react-router-dom';
import {
  Monitor,
  FileImage,
  LayoutDashboard,
  LogOut,
  Tag,
  ListVideo,
  Puzzle,
  Settings,
  Menu,
  X,
  FileText,
  Building2,
  BarChart3,
  Folder,
  Calendar,
  Languages,
  FileCode,
  Shield,
  Hotel,
  CloudRain,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useUIStore } from '@/lib/stores/uiStore';
import { useAuthStore } from '@/lib/stores/authStore';
import { useLogout } from '@/features/auth/hooks/useAuth';
import { ThemeSwitcher, LanguageSwitcher } from '@/shared/components';

export default function Sidebar() {
  const location = useLocation();
  const { t } = useTranslation();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { user } = useAuthStore();
  const logoutMutation = useLogout();

  const navigation = [
    { name: t('navigation.dashboard'), href: '/dashboard', icon: LayoutDashboard },
    { name: t('navigation.devices'), href: '/devices', icon: Monitor },
    { name: t('navigation.deviceGroups'), href: '/device-groups', icon: Folder },
    { name: t('navigation.contents'), href: '/contents', icon: FileImage },
    { name: t('navigation.playlists'), href: '/playlists', icon: ListVideo },
    { name: t('navigation.schedules'), href: '/schedules', icon: Calendar },
    { name: t('navigation.widgets'), href: '/widgets', icon: Puzzle },
    { name: t('navigation.templates'), href: '/templates', icon: FileCode },
    { name: t('navigation.translations'), href: '/translations', icon: Languages },
    { name: t('navigation.tags'), href: '/tags', icon: Tag },
    { name: t('navigation.analytics'), href: '/analytics', icon: BarChart3 },
    { name: t('navigation.auditLogs'), href: '/audit-logs', icon: FileText },
    { name: 'Active Sessions', href: '/sessions', icon: Shield },
    { name: 'Roles & Permissions', href: '/roles', icon: Shield },
    { name: 'PMS Integration', href: '/pms', icon: Hotel },
    { name: 'Weather Service', href: '/weather', icon: CloudRain },
    { name: t('navigation.settings'), href: '/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile Burger Menu Button */}
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-[60] lg:hidden p-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg shadow-lg"
        aria-label="Toggle menu"
      >
        {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-800 shadow-xl border-r border-gray-200 dark:border-gray-700 z-50 transform transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 bg-blue-600 dark:bg-blue-700">
            <h1 className="text-xl font-bold text-white">{t('app.name')}</h1>
          </div>

          {/* User Info */}
          {user && (
            <div className="px-4 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {user.full_name || user.username}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {user.role}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={toggleSidebar}
                  className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Theme, Language & Logout */}
          <div className="p-4 border-t dark:border-gray-700 space-y-3">
            {/* Theme & Language Switchers */}
            <div className="flex items-center justify-center gap-2">
              <LanguageSwitcher />
              <ThemeSwitcher />
            </div>

            {/* Logout */}
            <button
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
              className="flex items-center w-full px-4 py-3 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors disabled:opacity-50"
            >
              <LogOut className="w-5 h-5 mr-3" />
              <span className="font-medium">
                {logoutMutation.isPending ? t('auth.loggingOut') : t('common.logout')}
              </span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
