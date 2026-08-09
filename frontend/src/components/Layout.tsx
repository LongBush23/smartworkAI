import { useState, useEffect, useRef } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Users, LogOut, Bell, Shield, Menu, X,
  Award, FileText, BarChart2, ListChecks, ClipboardCheck, ClipboardList, Network,
  ShieldAlert, PanelLeftClose, PanelLeftOpen,
} from 'lucide-react';
import api from '../lib/api';
import { CLEARANCE_LABELS } from '../lib/task-api';

const ROLE_LABELS: Record<string, string> = {
  admin: 'Quản trị hệ thống',
  director: 'Lãnh đạo đơn vị',
  leader: 'Lãnh đạo, chỉ huy',
  staff: 'Cán bộ, chiến sĩ',
};

const KHOA_GHIM = 'navbar_ghim';

/** Một mục điều hướng. `quyen` quyết định ai nhìn thấy. */
interface MucDieuHuong {
  to: string;
  nhan: string;
  Icon: typeof LayoutDashboard;
  quyen?: 'leaderPlus' | 'directorPlus' | 'admin';
}

const NHOM_DIEU_HUONG: { tieuDe: string; muc: MucDieuHuong[] }[] = [
  {
    tieuDe: 'Tổng quan',
    muc: [
      { to: '/', nhan: 'Trang chủ', Icon: LayoutDashboard },
      { to: '/organization', nhan: 'Cơ cấu tổ chức', Icon: Network },
    ],
  },
  {
    tieuDe: 'Nhiệm vụ công tác',
    muc: [
      { to: '/tasks', nhan: 'Nhiệm vụ được giao', Icon: ListChecks },
      { to: '/kpi/catalog', nhan: 'Danh mục nhiệm vụ', Icon: ClipboardList, quyen: 'directorPlus' },
    ],
  },
  {
    tieuDe: 'Đánh giá KPI',
    muc: [
      { to: '/kpi', nhan: 'Tổng quan KPI', Icon: BarChart2 },
      { to: '/kpi/evaluate', nhan: 'Quy trình đánh giá', Icon: FileText },
      { to: '/kpi/criteria', nhan: 'Tiêu chí chung (E)', Icon: ClipboardCheck, quyen: 'leaderPlus' },
      { to: '/kpi/results', nhan: 'Kết quả xếp loại', Icon: Award },
    ],
  },
  {
    tieuDe: 'Quản lý',
    muc: [
      { to: '/employees', nhan: 'Cán bộ', Icon: Users, quyen: 'directorPlus' },
      { to: '/quality-review', nhan: 'Rà soát chất lượng', Icon: ShieldAlert, quyen: 'directorPlus' },
      { to: '/audit-logs', nhan: 'Nhật ký hệ thống', Icon: Shield, quyen: 'admin' },
    ],
  },
];

const Layout = () => {
  const location = useLocation();
  const [user, setUser] = useState<any>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [moTrenDienThoai, setMoTrenDienThoai] = useState(false);

  // Ghim = luôn mở. Không ghim = dải biểu tượng, rê chuột mới bung.
  const [ghim, setGhim] = useState(() => localStorage.getItem(KHOA_GHIM) !== 'false');
  const [dangRe, setDangRe] = useState(false);
  const hoanRe = useRef<number | null>(null);

  useEffect(() => { localStorage.setItem(KHOA_GHIM, String(ghim)); }, [ghim]);

  // Bung ngay khi rê vào, nhưng thu lại có độ trễ nhỏ: chuột đi ngang qua mép
  // trái mà thanh nhấp nháy liên tục thì rất khó chịu.
  const vaoVungThanh = () => {
    if (hoanRe.current) { window.clearTimeout(hoanRe.current); hoanRe.current = null; }
    setDangRe(true);
  };
  const roiVungThanh = () => {
    hoanRe.current = window.setTimeout(() => setDangRe(false), 180);
  };
  useEffect(() => () => { if (hoanRe.current) window.clearTimeout(hoanRe.current); }, []);

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

  useEffect(() => { setMoTrenDienThoai(false); }, [location.pathname]);

  const handleLogout = async () => {
    try { await api.post('/auth/logout'); } catch { /* vẫn xoá token phía client */ }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
  };

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  const userRole = user?.role || 'staff';
  const isLeaderPlus = ['leader', 'director', 'admin'].includes(userRole);
  const isDirectorPlus = ['director', 'admin'].includes(userRole);
  const isAdmin = userRole === 'admin';
  const clearance = user?.clearance_level ?? 0;

  const duocXem = (quyen?: MucDieuHuong['quyen']) => {
    if (!quyen) return true;
    if (quyen === 'leaderPlus') return isLeaderPlus;
    if (quyen === 'directorPlus') return isDirectorPlus;
    return isAdmin;
  };

  // Trên điện thoại luôn hiện đầy đủ; trên máy tính thì tuỳ ghim / rê chuột.
  const bung = ghim || dangRe;

  return (
    <div className="h-screen flex overflow-hidden">
      {moTrenDienThoai && (
        <div className="fixed inset-0 bg-black/60 z-30 md:hidden" onClick={() => setMoTrenDienThoai(false)} />
      )}

      {/*
        Khi không ghim, thanh chỉ chiếm 4rem trong luồng bố cục nhưng phần bung
        ra nổi lên trên nội dung. Nhờ vậy rê chuột không làm cả trang chạy sang
        phải — thứ gây mất phương hướng nhất khi dùng kiểu thanh bung/thu.
      */}
      <div className={`hidden md:block shrink-0 transition-all duration-200 ${ghim ? 'w-64' : 'w-16'}`} />

      <aside
        onMouseEnter={vaoVungThanh}
        onMouseLeave={roiVungThanh}
        className={`fixed inset-y-0 left-0 z-40 bg-navy-900 flex flex-col h-screen
          transition-[width,transform] duration-200
          ${bung ? 'w-64' : 'w-16'}
          ${!ghim && dangRe ? 'shadow-2xl shadow-black/40' : ''}
          ${moTrenDienThoai ? 'translate-x-0 w-64' : '-translate-x-full'} md:translate-x-0`}
      >
        {/* Tiêu đề */}
        <div className={`h-14 flex items-center border-b border-navy-700 shrink-0 ${bung ? 'px-3' : 'px-0 justify-center'}`}>
          {bung ? (
            <>
              <div className="min-w-0 flex-1">
                <h1 className="text-[13px] font-bold text-white leading-tight tracking-wide truncate">
                  HỆ THỐNG TÍNH ĐIỂM KPI
                </h1>
                <p className="text-[9px] text-gold-300 leading-tight tracking-wider">CÔNG AN NHÂN DÂN</p>
              </div>
              <button
                onClick={() => setGhim(!ghim)}
                title={ghim ? 'Thu gọn thanh điều hướng' : 'Ghim thanh điều hướng'}
                className="hidden md:block p-1 text-navy-400 hover:text-gold-300 shrink-0"
              >
                {ghim ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
              </button>
              <button onClick={() => setMoTrenDienThoai(false)} className="md:hidden p-1 text-navy-300 hover:text-white">
                <X size={20} />
              </button>
            </>
          ) : (
            <Shield size={20} className="text-gold-400" />
          )}
        </div>

        {/*
          min-h-0 để vùng này co lại được khi màn hình thấp, nhờ đó thẻ cán bộ ở
          đáy không bị đẩy khuất. Khoảng cách giữa các mục giảm dần theo chiều
          cao màn hình để 11 mục vừa trong một màn không cần cuộn.
        */}
        <nav className="nav-thich-ung flex-1 min-h-0 overflow-y-auto overflow-x-hidden custom-scrollbar py-1.5 px-1.5 space-y-px">
          {NHOM_DIEU_HUONG.map(nhom => {
            const muc = nhom.muc.filter(m => duocXem(m.quyen));
            if (muc.length === 0) return null;
            return (
              <div key={nhom.tieuDe} className="nav-nhom pt-1.5 first:pt-0">
                {bung ? (
                  <p className="section-label px-2 pt-1 pb-0.5 !text-navy-500 truncate">{nhom.tieuDe}</p>
                ) : (
                  <div className="mx-2 my-1.5 border-t border-navy-800" />
                )}
                {muc.map(({ to, nhan, Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    title={bung ? undefined : nhan}
                    className={`flex items-center rounded-sm text-[13px] transition-colors border-l-2
                      ${bung ? 'gap-2.5 px-2.5 py-[7px]' : 'justify-center px-0 py-2'}
                      ${isActive(to)
                        ? 'bg-navy-800 text-white border-gold-400 font-medium'
                        : 'text-navy-200 border-transparent hover:bg-navy-800/60 hover:text-white'}`}
                  >
                    <Icon size={16} className="shrink-0" />
                    {bung && <span className="truncate">{nhan}</span>}
                  </Link>
                ))}
              </div>
            );
          })}
        </nav>

        {/* Thẻ cán bộ */}
        <div className="border-t border-navy-700 shrink-0">
          <Link
            to="/profile"
            title={bung ? undefined : user?.name}
            className={`flex items-center hover:bg-navy-800 transition-colors ${bung ? 'gap-2.5 px-2.5 py-2' : 'justify-center py-2'}`}
          >
            <div className="w-8 h-8 rounded-sm bg-navy-600 text-white flex items-center justify-center font-bold text-xs shrink-0 overflow-hidden">
              {user?.avatar
                ? <img src={user.avatar} alt="" className="w-full h-full object-cover" />
                : (user?.name ? user.name.charAt(0).toUpperCase() : 'U')}
            </div>
            {bung && (
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-white truncate">{user?.name || 'Tài khoản'}</p>
                <p className="text-[10px] text-navy-300 truncate">
                  {[user?.rank, user?.position].filter(Boolean).join(' · ') || ROLE_LABELS[userRole]}
                </p>
              </div>
            )}
          </Link>

          {/* Cấp độ tiếp cận tài liệu — thu gọn thì chỉ còn khiên đổi màu */}
          <div className={bung ? 'px-2.5 pb-1.5' : 'flex justify-center pb-1.5'}>
            <div
              title={`Tiếp cận: ${CLEARANCE_LABELS[clearance] ?? 'Tài liệu thường'}`}
              className={`flex items-center gap-1.5 text-[10px] text-navy-300 bg-navy-800 rounded-sm ${bung ? 'px-2 py-1' : 'p-1.5'}`}
            >
              <Shield size={11} className={clearance > 0 ? 'text-gold-400' : 'text-navy-400'} />
              {bung && <span className="truncate">Tiếp cận: {CLEARANCE_LABELS[clearance] ?? 'Tài liệu thường'}</span>}
            </div>
          </div>

          <button
            onClick={handleLogout}
            title={bung ? undefined : 'Đăng xuất'}
            className={`flex w-full items-center text-crimson-300 hover:bg-crimson-900/40 hover:text-crimson-200 transition-colors text-[13px] border-t border-navy-800
              ${bung ? 'gap-2.5 px-2.5 py-2' : 'justify-center py-2'}`}
          >
            <LogOut size={15} className="shrink-0" />
            {bung && <span>Đăng xuất</span>}
          </button>
        </div>
      </aside>

      {/* Nội dung chính */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-12 shrink-0 bg-white border-b border-navy-200 flex items-center justify-between px-3 md:px-5">
          <div className="flex items-center gap-2.5 min-w-0">
            <button
              onClick={() => setMoTrenDienThoai(true)}
              className="md:hidden p-1.5 -ml-1.5 text-navy-600 hover:bg-navy-50 rounded-sm"
            >
              <Menu size={20} />
            </button>
            <h2 className="text-[13px] font-semibold text-navy-800 truncate">
              Tính điểm KPI trong đánh giá, xếp loại chất lượng tập thể, cá nhân
            </h2>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Link to="/notifications" className="relative p-2 rounded-sm hover:bg-navy-50 transition-colors">
              <Bell size={18} className="text-navy-600" />
              {unreadCount > 0 && (
                <span className="absolute top-0.5 right-0.5 bg-crimson-600 text-white text-[10px] font-bold min-w-4 h-4 px-1 rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>
          </div>
        </header>

        <main className="flex-1 p-4 md:p-5 overflow-y-auto overflow-x-hidden custom-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
