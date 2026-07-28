import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { User, KeyRound, Save, Award, Building2 } from 'lucide-react';
import api from '../lib/api';
import { kpiApi, KPI_GROUP_LABELS, KPI_GROUP_COLORS } from '../lib/kpi-api';
import type { KPIEvaluation } from '../lib/kpi-api';

const ROLE_LABELS: Record<string, string> = {
  admin: 'Quản trị hệ thống',
  director: 'Lãnh đạo đơn vị',
  leader: 'Lãnh đạo, chỉ huy',
  staff: 'Cán bộ, chiến sĩ',
};

const QUARTERS: Record<number, number[]> = {
  1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12],
};

const Profile = () => {
  const [me, setMe] = useState<any>(null);
  const [departmentName, setDepartmentName] = useState('—');
  const [evaluations, setEvaluations] = useState<KPIEvaluation[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'info' | 'kpi' | 'password'>('info');

  const [form, setForm] = useState({ name: '', email: '', position: '', rank: '', bio: '' });
  const [pwd, setPwd] = useState({ old_password: '', new_password: '', confirm: '' });

  const year = new Date().getFullYear();

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      setLoading(true);
      const meRes = await api.get('/auth/me');
      setMe(meRes.data);
      setForm({
        name: meRes.data.name ?? '',
        email: meRes.data.email ?? '',
        position: meRes.data.position ?? '',
        rank: meRes.data.rank ?? '',
        bio: meRes.data.bio ?? '',
      });

      if (meRes.data.department_id) {
        api.get(`/departments/${meRes.data.department_id}`)
          .then(r => setDepartmentName(r.data.name))
          .catch(() => setDepartmentName('—'));
      }

      const evals = await kpiApi
        .getEvaluations({ target_id: meRes.data._id, period_year: year })
        .catch(() => []);
      setEvaluations(evals);
    } catch (error) {
      console.error('Không tải được hồ sơ cán bộ', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.put('/auth/profile', form);
      toast.success('Đã cập nhật hồ sơ');
      load();
    } catch { toast.error('Không cập nhật được hồ sơ'); }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (pwd.new_password !== pwd.confirm) {
      toast.error('Mật khẩu mới nhập lại không khớp');
      return;
    }
    if (pwd.new_password.length < 6) {
      toast.error('Mật khẩu mới phải từ 6 ký tự');
      return;
    }
    try {
      await api.post('/auth/change-password', {
        old_password: pwd.old_password,
        new_password: pwd.new_password,
      });
      toast.success('Đã đổi mật khẩu');
      setPwd({ old_password: '', new_password: '', confirm: '' });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Không đổi được mật khẩu');
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  const monthly = evaluations
    .filter(e => e.period_type === 'monthly' && e.overall_status === 'approved' && e.approval?.kpi_score != null)
    .sort((a, b) => (a.period_month ?? 0) - (b.period_month ?? 0));

  const avg = (scores: number[]) =>
    scores.length ? scores.reduce((s, v) => s + v, 0) / scores.length : null;

  const yearlyAvg = avg(monthly.map(e => Number(e.approval.kpi_score)));

  const isCommander = me?.role === 'leader' || me?.role === 'director';

  const tabClass = (t: string) =>
    `px-4 py-2.5 text-sm font-medium border-b-2 transition ${
      tab === t ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'
    }`;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Hồ sơ cán bộ</h1>

      {/* Thẻ thông tin */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-blue-600 text-white flex items-center justify-center text-2xl font-bold shrink-0 overflow-hidden">
            {me?.avatar
              ? <img src={me.avatar} alt="" className="w-full h-full object-cover" />
              : (me?.name?.charAt(0).toUpperCase() ?? 'U')}
          </div>
          <div className="min-w-0">
            <h2 className="text-xl font-bold text-gray-800">{me?.name}</h2>
            <p className="text-sm text-gray-600">
              {[me?.rank, me?.position].filter(Boolean).join(' · ') || ROLE_LABELS[me?.role] || '—'}
            </p>
            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
              <Building2 size={12} /> {departmentName}
              <span className="mx-1">·</span>
              {ROLE_LABELS[me?.role] ?? me?.role}
            </p>
          </div>
          {isCommander && (
            <span className="ml-auto shrink-0 px-3 py-1.5 bg-amber-50 text-amber-800 border border-amber-200 rounded-lg text-xs font-medium">
              Lãnh đạo, chỉ huy — KPI theo 04 tiêu chí
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="flex border-b border-gray-200 px-4 overflow-x-auto">
          <button onClick={() => setTab('info')} className={tabClass('info')}>Thông tin cá nhân</button>
          <button onClick={() => setTab('kpi')} className={tabClass('kpi')}>Điểm KPI của tôi</button>
          <button onClick={() => setTab('password')} className={tabClass('password')}>Đổi mật khẩu</button>
        </div>

        <div className="p-6">
          {tab === 'info' && (
            <form onSubmit={handleSaveProfile} className="space-y-4 max-w-2xl">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên *</label>
                  <input
                    required value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Thư điện tử *</label>
                  <input
                    required type="email" value={form.email}
                    onChange={e => setForm({ ...form, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cấp bậc hàm</label>
                  <input
                    value={form.rank}
                    onChange={e => setForm({ ...form, rank: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Chức vụ</label>
                  <input
                    value={form.position}
                    onChange={e => setForm({ ...form, position: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Giới thiệu</label>
                <textarea
                  rows={3} value={form.bio}
                  onChange={e => setForm({ ...form, bio: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div className="flex items-center gap-2 pt-1 text-xs text-gray-500">
                <User size={14} />
                Tên đăng nhập <strong className="text-gray-700">{me?.username}</strong> và thẩm quyền do quản trị hệ thống quản lý.
              </div>
              <button type="submit" className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                <Save size={16} /> Lưu thay đổi
              </button>
            </form>
          )}

          {tab === 'kpi' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4">
                  <p className="text-xs text-indigo-700">KPI bình quân năm {year}</p>
                  <p className="text-3xl font-bold text-indigo-700 mt-1">
                    {yearlyAvg != null ? yearlyAvg.toFixed(2) : '–'}
                  </p>
                  <p className="text-[11px] text-indigo-600 mt-1">
                    Bình quân {monthly.length} tháng đã phê duyệt
                  </p>
                </div>
                {[1, 2, 3, 4].map(q => {
                  const qScores = monthly
                    .filter(e => QUARTERS[q].includes(e.period_month ?? 0))
                    .map(e => Number(e.approval.kpi_score));
                  const qAvg = avg(qScores);
                  if (qAvg == null) return null;
                  return (
                    <div key={q} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-xs text-gray-600">KPI Quý {q}</p>
                      <p className="text-2xl font-bold text-gray-800 mt-1">{qAvg.toFixed(2)}</p>
                      <p className="text-[11px] text-gray-500 mt-1">{qScores.length} tháng</p>
                    </div>
                  );
                })}
              </div>

              {monthly.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">
                  Chưa có kỳ đánh giá nào được phê duyệt trong năm {year}.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200 text-gray-600">
                        <th className="p-3 font-medium">Kỳ</th>
                        <th className="p-3 font-medium text-center">A</th>
                        <th className="p-3 font-medium text-center">B</th>
                        <th className="p-3 font-medium text-center">C</th>
                        {isCommander && <th className="p-3 font-medium text-center">D</th>}
                        <th className="p-3 font-medium text-center">KPI</th>
                        <th className="p-3 font-medium text-center">E</th>
                        <th className="p-3 font-medium text-center">Tổng điểm</th>
                        <th className="p-3 font-medium text-center">Xếp nhóm</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {monthly.map(e => {
                        const a = e.approval ?? {};
                        const g = e.general_criteria ?? {};
                        const p = (v: any) => v != null ? (Number(v) * 100).toFixed(1) + '%' : '–';
                        return (
                          <tr key={e.id} className="hover:bg-gray-50">
                            <td className="p-3 font-medium text-gray-800">Tháng {e.period_month}</td>
                            <td className="p-3 text-center text-gray-700">{p(a.score_A)}</td>
                            <td className="p-3 text-center text-gray-700">{p(a.score_B)}</td>
                            <td className="p-3 text-center text-gray-700">{p(a.score_C)}</td>
                            {isCommander && <td className="p-3 text-center text-gray-700">{p(a.score_D)}</td>}
                            <td className="p-3 text-center font-bold text-indigo-700">{Number(a.kpi_score).toFixed(1)}</td>
                            <td className="p-3 text-center text-gray-700">{g.total_E != null ? Number(g.total_E).toFixed(1) : '–'}</td>
                            <td className="p-3 text-center font-bold text-amber-700">
                              {g.total_final_score != null ? Number(g.total_final_score).toFixed(1) : '–'}
                            </td>
                            <td className="p-3 text-center">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${KPI_GROUP_COLORS[a.kpi_group] ?? ''}`}>
                                {KPI_GROUP_LABELS[a.kpi_group] ?? a.kpi_group}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              <p className="text-xs text-gray-500 flex items-start gap-2">
                <Award size={14} className="mt-0.5 shrink-0" />
                Điểm KPI hằng quý, hằng năm được xác định bằng bình quân điểm KPI hằng tháng
                (mục 5.2 Hướng dẫn số 20-HD/ĐUCA).
              </p>
            </div>
          )}

          {tab === 'password' && (
            <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu hiện tại *</label>
                <input
                  required type="password" value={pwd.old_password}
                  onChange={e => setPwd({ ...pwd, old_password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu mới *</label>
                <input
                  required type="password" value={pwd.new_password}
                  onChange={e => setPwd({ ...pwd, new_password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nhập lại mật khẩu mới *</label>
                <input
                  required type="password" value={pwd.confirm}
                  onChange={e => setPwd({ ...pwd, confirm: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <button type="submit" className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                <KeyRound size={16} /> Đổi mật khẩu
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
