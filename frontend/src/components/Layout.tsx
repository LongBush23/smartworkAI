import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Users, LogOut, Bell, Shield, Menu, X,
  Award, FileText, BarChart2, ListChecks, ClipboardCheck, ClipboardList, Network, ShieldAlert,
} from 'lucide-react';
import api from '../lib/api';
import { CLEARANCE_LABELS } from '../lib/task-api';

const ROLE_LABELS: Record<string, string> = {
  admin: 'Quản trị hệ thống',
  director: 'Lãnh đạo đơn vị',
  leader: 'Lãnh đạo, chỉ huy',
  staff: 'Cán bộ, chiến sĩ',
};

const Layout = () => {
  const location = useLocation();
  const [user, setUser] = useState<any>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    api.get('/auth/me').then(res => setUser(res.data)).catch(() => {});

    const fetchUnreadCount = () => {
      api.get('/notifications/unread-count').then(res => setUnreadCount(res.data.count)).catch(() => {});
    };
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    window.addEventListener('notificationRead', fetchUnreadCount);
    return () => {
      clearInterval(interval);
      window.removeEventListener('notificationRead', fetchUnreadCount);
    };
  }, []);

  useEffect(() => { setIsMobileMenuOpen(false); }, [location.pathname]);

  const handleLogout = async () => {
    try { await api.post('/auth/logout'); } catch { /* vẫn xoá token phía client */ }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
  };

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  const linkClass = (path: string) =>
    `flex items-center gap-2.5 px-3 py-2 rounded-sm text-sm transition-colors border-l-2 ${
      isActive(path)
        ? 'bg-navy-800 text-white border-gold-400 font-medium'
        : 'text-navy-200 border-transparent hover:bg-navy-800/60 hover:text-white'
    }`;

  const userRole = user?.role || 'staff';
  const isLeaderPlus = ['leader', 'director', 'admin'].includes(userRole);
  const isDirectorPlus = ['director', 'admin'].includes(userRole);
  const isAdmin = userRole === 'admin';
  const clearance = user?.clearance_level ?? 0;

  return (
    <div className="min-h-screen flex">
      {isMobileMenuOpen && (
        <div className="fixed inset-0 bg-black/60 z-30 md:hidden" onClick={() => setIsMobileMenuOpen(false)} />
      )}

      {/* Thanh điều hướng */}
      <aside className={`fixed inset-y-0 left-0 z-40 w-64 bg-navy-900 flex flex-col h-screen transform transition-transform duration-200 md:relative md:translate-x-0 ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="h-16 flex items-center justify-between px-4 border-b border-navy-700 shrink-0">
          <div className="min-w-0">
            <h1 className="text-sm font-bold text-white leading-tight tracking-wide">
              HỆ THỐNG TÍNH ĐIỂM KPI
            </h1>
            <p className="text-[10px] text-gold-300 leading-tight mt-0.5 tracking-wider">
              CÔNG AN NHÂN DÂN
            </p>
          </div>
          <button onClick={() => setIsMobileMenuOpen(false)} className="md:hidden text-navy-300 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <nav className="p-2 space-y-0.5 flex-1 overflow-y-auto custom-scrollbar">
          <p className="section-label px-3 pt-3 pb-1 !text-navy-500">Tổng quan</p>
          <Link to="/" className={linkClass('/')}>
            <LayoutDashboard size={17} /> <span>Trang chủ</span>
          </Link>
          <Link to="/organization" className={linkClass('/organization')}>
            <Network size={17} /> <span>Cơ cấu tổ chức</span>
          </Link>

          <p className="section-label px-3 pt-4 pb-1 !text-navy-500">Nhiệm vụ công tác</p>
          <Link to="/tasks" className={linkClass('/tasks')}>
            <ListChecks size={17} /> <span>Nhiệm vụ được giao</span>
          </Link>
          {isDirectorPlus && (
            <Link to="/kpi/catalog" className={linkClass('/kpi/catalog')}>
              <ClipboardList size={17} /> <span>Danh mục nhiệm vụ</span>
            </Link>
          )}

          <p className="section-label px-3 pt-4 pb-1 !text-navy-500">Đánh giá KPI</p>
          <Link to="/kpi" className={linkClass('/kpi')}>
            <BarChart2 size={17} /> <span>Tổng quan KPI</span>
          </Link>
          <Link to="/kpi/evaluate" className={linkClass('/kpi/evaluate')}>
            <FileText size={17} /> <span>Quy trình đánh giá</span>
          </Link>
          {isLeaderPlus && (
            <Link to="/kpi/criteria" className={linkClass('/kpi/criteria')}>
              <ClipboardCheck size={17} /> <span>Tiêu chí chung (E)</span>
            </Link>
          )}
          <Link to="/kpi/results" className={linkClass('/kpi/results')}>
            <Award size={17} /> <span>Kết quả xếp loại</span>
          </Link>

          {(isDirectorPlus || isAdmin) && (
            <>
              <p className="section-label px-3 pt-4 pb-1 !text-navy-500">Quản lý</p>
              {isDirectorPlus && (
                <>
                  <Link to="/employees" className={linkClass('/employees')}>
                    <Users size={17} /> <span>Cán bộ</span>
                  </Link>
                  <Link to="/quality-review" className={linkClass('/quality-review')}>
                    <ShieldAlert size={17} /> <span>Rà soát chất lượng</span>
                  </Link>
                </>
              )}
              {isAdmin && (
                <Link to="/audit-logs" className={linkClass('/audit-logs')}>
                  <Shield size={17} /> <span>Nhật ký hệ thống</span>
                </Link>
              )}
            </>
          )}
        </nav>

        {/* Thẻ cán bộ */}
        <div className="border-t border-navy-700 shrink-0">
          <Link to="/profile" className="flex items-center gap-2.5 px-3 py-3 hover:bg-navy-800 transition-colors">
            <div className="w-9 h-9 rounded-sm bg-navy-600 text-white flex items-center justify-center font-bold text-sm shrink-0 overflow-hidden">
              {user?.avatar
                ? <img src={user.avatar} alt="" className="w-full h-full object-cover" />
                : (user?.name ? user.name.charAt(0).toUpperCase() : 'U')}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name || 'Tài khoản'}</p>
              <p className="text-[11px] text-navy-300 truncate">
                {[user?.rank, user?.position].filter(Boolean).join(' · ') || ROLE_LABELS[userRole]}
              </p>
            </div>
          </Link>
          {/* Cấp độ tiếp cận tài liệu */}
          <div className="px-3 pb-2">
            <div className="flex items-center gap-1.5 text-[10px] text-navy-300 bg-navy-800 px-2 py-1 rounded-sm">
              <Shield size={11} className={clearance > 0 ? 'text-gold-400' : 'text-navy-400'} />
              <span>Tiếp cận: {CLEARANCE_LABELS[clearance] ?? 'Tài liệu thường'}</span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2.5 px-3 py-2.5 text-crimson-300 hover:bg-crimson-900/40 hover:text-crimson-200 transition-colors text-sm border-t border-navy-800"
          >
            <LogOut size={16} /> <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* Nội dung chính */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 shrink-0 bg-white border-b border-navy-200 flex items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-1.5 -ml-1.5 text-navy-600 hover:bg-navy-50 rounded-sm"
            >
              <Menu size={22} />
            </button>
            <h2 className="text-sm font-semibold text-navy-800 truncate">
              Tính điểm KPI trong đánh giá, xếp loại chất lượng tập thể, cá nhân
            </h2>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Link to="/notifications" className="relative p-2 rounded-sm hover:bg-navy-50 transition-colors">
              <Bell size={19} className="text-navy-600" />
              {unreadCount > 0 && (
                <span className="absolute top-0.5 right-0.5 bg-crimson-600 text-white text-[10px] font-bold min-w-4 h-4 px-1 rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>
          </div>
        </header>

        <main className="flex-1 p-5 overflow-y-auto overflow-x-hidden custom-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
