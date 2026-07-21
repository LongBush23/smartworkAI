import React, { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Briefcase, CheckSquare, Users, LogOut, UserCircle, Bell, ClipboardCheck, Shield } from 'lucide-react';
import api from '../lib/api';

const ROLE_LABELS: Record<string, string> = {
  admin: 'Quản trị viên',
  director: 'Trưởng phòng',
  leader: 'Nhóm trưởng',
  staff: 'Chuyên viên',
};

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState<any>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    api.get('/auth/me').then(res => setUser(res.data)).catch(() => {});
    
    const fetchUnreadCount = () => {
      api.get('/notifications/unread-count').then(res => setUnreadCount(res.data.count)).catch(() => {});
    };
    
    fetchUnreadCount();
    
    // Poll for new notifications every 30s
    const interval = setInterval(fetchUnreadCount, 30000);
    
    // Listen for manual read events from Notifications page
    window.addEventListener('notificationRead', fetchUnreadCount);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('notificationRead', fetchUnreadCount);
    };
  }, []);

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {}
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
  };

  const isActive = (path: string) => location.pathname === path;
  const linkClass = (path: string) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
      isActive(path) ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-gray-600 hover:bg-gray-100'
    }`;

  const userRole = user?.role || 'staff';
  const isLeaderPlus = ['leader', 'director', 'admin'].includes(userRole);
  const isDirectorPlus = ['director', 'admin'].includes(userRole);
  const isAdmin = userRole === 'admin';

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shadow-sm h-screen sticky top-0">
        <div className="h-16 flex items-center px-6 border-b border-gray-200 shrink-0">
          <h1 className="text-xl font-bold text-blue-600">SmartWork AI</h1>
        </div>
        <nav className="p-3 space-y-1 flex-1">
          <p className="text-xs uppercase text-gray-400 font-semibold px-3 pt-2 pb-1">Tổng quan</p>
          <Link to="/" className={linkClass('/')}>
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </Link>

          <p className="text-xs uppercase text-gray-400 font-semibold px-3 pt-4 pb-1">Công việc</p>
          <Link to="/projects" className={linkClass('/projects')}>
            <Briefcase size={20} />
            <span>Dự án</span>
          </Link>
          <Link to="/tasks" className={linkClass('/tasks')}>
            <CheckSquare size={20} />
            <span>Công việc</span>
          </Link>
          
          {isLeaderPlus && (
            <Link to="/requests" className={linkClass('/requests')}>
              <ClipboardCheck size={20} />
              <span>Yêu cầu tham gia</span>
              {unreadCount > 0 && (
                <span className="ml-auto bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">{unreadCount}</span>
              )}
            </Link>
          )}

          {isDirectorPlus && (
            <>
              <p className="text-xs uppercase text-gray-400 font-semibold px-3 pt-4 pb-1">Quản lý</p>
              <Link to="/employees" className={linkClass('/employees')}>
                <Users size={20} />
                <span>Nhân sự</span>
              </Link>
            </>
          )}

          {isAdmin && (
            <Link to="/audit-logs" className={linkClass('/audit-logs')}>
              <Shield size={20} />
              <span>Nhật ký Kiểm toán</span>
            </Link>
          )}
        </nav>
        
        {/* User Card */}
        <div className="p-4 border-t border-gray-200 space-y-3">
          <Link to="/profile" className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
            <div className="w-9 h-9 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm overflow-hidden">
              {user?.avatar ? (
                <img src={user.avatar} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                user?.name ? user.name.charAt(0).toUpperCase() : 'U'
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-800 truncate">{user?.name || 'Tài khoản'}</p>
              <p className="text-xs text-gray-500">{ROLE_LABELS[userRole] || userRole}</p>
            </div>
          </Link>
          <button 
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-3 py-2 text-red-600 rounded-lg hover:bg-red-50 transition-colors text-sm"
          >
            <LogOut size={18} />
            <span className="font-medium">Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 shrink-0 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800">Cơ quan Quản lý Tỉnh Đắk Lắk</h2>
          <div className="flex items-center gap-4">
            {/* Notification Bell */}
            <Link to="/notifications" className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
              <Bell size={22} className="text-gray-600" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>
            
            <Link to="/profile" className="flex items-center gap-2 hover:bg-gray-50 px-3 py-1.5 rounded-lg transition-colors">
              <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm overflow-hidden">
                {user?.avatar ? (
                  <img src={user.avatar} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  user?.name ? user.name.charAt(0).toUpperCase() : 'U'
                )}
              </div>
              <div className="hidden md:block">
                <span className="text-sm font-medium text-gray-700">{user?.name || 'Tài khoản'}</span>
              </div>
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-y-auto overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
