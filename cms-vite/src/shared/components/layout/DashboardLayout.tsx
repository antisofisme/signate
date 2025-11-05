/**
 * Dashboard Layout Component
 *
 * LAYER 1: PRESENTATION
 * Main layout wrapper for authenticated pages
 */

import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { useUIStore } from '@/lib/stores/uiStore';
import { ToastContainer } from '@/lib/notifications/ToastContainer';

export default function DashboardLayout() {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="lg:ml-64 transition-all duration-300">
        {/* Topbar */}
        <Topbar />

        {/* Page Content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>

      {/* Toast Notifications */}
      <ToastContainer />
    </div>
  );
}
