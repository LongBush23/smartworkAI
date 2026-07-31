import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import {
  ArrowLeft, Shield, Lock, AlertTriangle, FileEdit, Bell,
  Building2, Mail, IdCard, CheckCircle2, Clock,
} from 'lucide-react';
import {
  taskApi, WORKLOAD_LABELS, WORKLOAD_COLORS, WORKLOAD_BAR, CLEARANCE_LABELS,
  TASK_STATUS_LABELS, TASK_STATUS_COLORS, CLASSIFICATION_LABELS, CLASSIFICATION_COLORS,
  PRODUCT_LABELS,
} from '../lib/task-api';
import type { EmployeeProfile, Task } from '../lib/task-api';
import { KPI_GROUP_LABELS, KPI_GROUP_COLORS, ROLE_LABELS } from '../lib/kpi-api';

const MONTHS = ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12'];

const EmployeeDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<EmployeeProfile | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { if (id) load(id); }, [id]);

  const load = async (employeeId: string) => {
    try {
      setLoading(true);
      const p = await taskApi.employeeProfile(employeeId);
      setProfile(p);
      const t = await taskApi.list({
        assignee_id: employeeId,
        period_month: p.period_month,
        period_year: p.period_year,
      }).catch(() => []);
      setTasks(t);
    } catch (error) {
      console.error('Không tải được hồ sơ cán bộ', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-600" /></div>;
  }
  if (!profile) {
    return <div className="bg-white border border-navy-200 rounded-sm p-12 text-center text-navy-500">Không tìm thấy cán bộ.</div>;
  }

  const p = profile;
  const now = new Date();
  const trend = p.kpi_history.map(h => ({
    name: MONTHS[(h.period_month ?? 1) - 1],
    kpi: Number(Number(h.kpi_score).toFixed(1)),
  }));

  const completionRate = p.tasks_assigned > 0
    ? (p.tasks_completed / p.tasks_assigned * 100).toFixed(0) : '0';

  return (
    <div className="space-y-4">
      <Link to="/organization" className="inline-flex items-center gap-1.5 text-sm text-navy-600 hover:text-navy-800 hover:underline">
        <ArrowLeft size={15} /> Cơ cấu tổ chức
      </Link>

      {/* Định danh */}
      <div className="bg-white border border-navy-200 rounded-sm overflow-hidden">
        <div className="bg-navy-700 text-white px-5 py-4 flex items-start gap-4">
          <div className="w-14 h-14 rounded-sm bg-navy-600 border border-navy-500 flex items-center justify-center text-2xl font-bold shrink-0">
            {p.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold truncate">{p.name}</h1>
            <p className="text-sm text-navy-200 mt-0.5">
              {[p.rank, p.position].filter(Boolean).join(' · ') || ROLE_LABELS[p.role]}
            </p>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-[11px] text-navy-300">
              {p.department_name && (
                <span className="inline-flex items-center gap-1"><Building2 size={11} /> {p.department_name}</span>
              )}
              {p.service_number && (
                <span className="inline-flex items-center gap-1"><IdCard size={11} /> {p.service_number}</span>
              )}
              {p.email && (
                <span className="inline-flex items-center gap-1"><Mail size={11} /> {p.email}</span>
              )}
            </div>
          </div>
          <div className="shrink-0 text-right space-y-1.5">
            <div className="inline-flex items-center gap-1.5 bg-navy-800 px-2.5 py-1 rounded-sm text-[11px]">
              <Shield size={12} className={p.clearance_level > 0 ? 'text-gold-400' : 'text-navy-400'} />
              <span className="text-navy-100">{CLEARANCE_LABELS[p.clearance_level]}</span>
            </div>
            {p.is_commander && (
              <p className="text-[10px] text-gold-300">Lãnh đạo, chỉ huy — KPI 04 tiêu chí</p>
            )}
          </div>
        </div>

        {/* Tình trạng sẵn sàng nhận nhiệm vụ */}
        <div className="px-5 py-4 border-b border-navy-100">
          <div className="flex items-center justify-between mb-2">
            <p className="section-label">Tình trạng nhận nhiệm vụ · Tháng {p.period_month}/{p.period_year}</p>
            <span className={`px-2 py-0.5 text-xs font-medium rounded-sm border ${WORKLOAD_COLORS[p.workload_status]}`}>
              {WORKLOAD_LABELS[p.workload_status]}
            </span>
          </div>
          <div className="h-3 bg-navy-100 rounded-sm overflow-hidden">
            <div
              className={`h-full ${WORKLOAD_BAR[p.workload_status]} transition-all`}
              style={{ width: `${Math.min(p.workload_percent, 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-1.5 text-[11px] text-navy-500 tabular">
            <span>Đang đảm nhận <strong className="text-navy-800">{p.open_points}</strong> điểm</span>
            <span className="font-medium text-navy-700">{p.workload_percent.toFixed(1)}%</span>
            <span>Định mức <strong className="text-navy-800">{p.capacity_points}</strong> điểm</span>
          </div>
        </div>
      </div>

      {/* Chỉ số chính */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
        {[
          { label: 'Nhiệm vụ được giao', value: p.tasks_assigned, sub: `${p.points_assigned} điểm`, color: 'text-navy-800' },
          { label: 'Đã hoàn thành', value: p.tasks_completed, sub: `${completionRate}% · ${p.points_completed} điểm`, color: 'text-emerald-700' },
          { label: 'Đang thực hiện', value: p.tasks_in_progress, sub: 'chưa hoàn thành', color: 'text-navy-600' },
          { label: 'Quá hạn', value: p.tasks_overdue, sub: 'cần xử lý ngay', color: p.tasks_overdue > 0 ? 'text-crimson-700' : 'text-navy-300' },
          { label: 'Lần phải sửa', value: p.total_revisions, sub: 'ảnh hưởng điểm B', color: 'text-navy-700' },
          { label: 'Lần bị nhắc nhở', value: p.total_reminders, sub: 'ảnh hưởng điểm C', color: 'text-navy-700' },
        ].map(s => (
          <div key={s.label} className="bg-white border border-navy-200 rounded-sm p-3">
            <p className="section-label leading-tight">{s.label}</p>
            <p className={`text-2xl font-bold tabular mt-1 ${s.color}`}>{s.value}</p>
            <p className="text-[10px] text-navy-400 mt-0.5">{s.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Diễn biến KPI */}
        <div className="lg:col-span-2 bg-white border border-navy-200 rounded-sm">
          <div className="px-4 py-2 border-b border-navy-200 bg-navy-50">
            <p className="section-label">Diễn biến điểm KPI năm {p.period_year}</p>
          </div>
          <div className="p-4">
            {trend.length === 0 ? (
              <p className="text-sm text-navy-400 text-center py-16">
                Chưa có kỳ nào được phê duyệt trong năm.
              </p>
            ) : (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trend} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="2 4" vertical={false} stroke="#e3eaf2" />
                    <XAxis dataKey="name" fontSize={11} stroke="#5c7fa8" />
                    <YAxis domain={[0, 120]} fontSize={11} stroke="#5c7fa8" />
                    <Tooltip formatter={(v) => [`${v} điểm`, 'KPI']} />
                    <Line type="monotone" dataKey="kpi" stroke="#1e3a5f" strokeWidth={2} dot={{ r: 3, fill: '#c2921f' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* Tổng hợp KPI */}
        <div className="bg-white border border-navy-200 rounded-sm">
          <div className="px-4 py-2 border-b border-navy-200 bg-navy-50">
            <p className="section-label">Tổng hợp KPI</p>
          </div>
          <div className="p-4 space-y-3">
            <div>
              <p className="text-[11px] text-navy-500">Kỳ gần nhất</p>
              <p className="text-3xl font-bold text-navy-800 tabular">
                {p.latest_kpi != null ? p.latest_kpi.toFixed(1) : '–'}
              </p>
              {p.latest_kpi_group && (
                <span className={`inline-block mt-1 px-2 py-0.5 text-[11px] rounded-sm border ${KPI_GROUP_COLORS[p.latest_kpi_group] ?? ''}`}>
                  {KPI_GROUP_LABELS[p.latest_kpi_group]}
                </span>
              )}
            </div>
            <div className="pt-3 border-t border-navy-100">
              <p className="text-[11px] text-navy-500">Bình quân năm {p.period_year}</p>
              <p className="text-2xl font-bold text-navy-700 tabular">
                {p.yearly_avg_kpi != null ? p.yearly_avg_kpi.toFixed(2) : '–'}
              </p>
              <p className="text-[10px] text-navy-400">{p.kpi_history.length} tháng đã phê duyệt</p>
            </div>
            {p.classified_tasks > 0 && (
              <div className="pt-3 border-t border-navy-100">
                <p className="text-[11px] text-navy-500 flex items-center gap-1">
                  <Lock size={11} className="text-crimson-600" /> Nhiệm vụ có độ mật
                </p>
                <p className="text-2xl font-bold text-crimson-700 tabular">{p.classified_tasks}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Nhiệm vụ trong kỳ */}
      <div className="bg-white border border-navy-200 rounded-sm overflow-hidden">
        <div className="px-4 py-2 border-b border-navy-200 bg-navy-50 flex items-center justify-between">
          <p className="section-label">Nhiệm vụ trong kỳ</p>
          <span className="text-xs text-navy-500 tabular">{tasks.length} nhiệm vụ</span>
        </div>
        {tasks.length === 0 ? (
          <p className="p-10 text-center text-sm text-navy-400">Không có nhiệm vụ nào trong kỳ này.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-white border-b border-navy-200 text-navy-500 text-xs">
                  <th className="text-left px-4 py-2 font-medium">Mã hiệu</th>
                  <th className="text-left px-3 py-2 font-medium">Nội dung</th>
                  <th className="text-left px-3 py-2 font-medium">Sản phẩm</th>
                  <th className="text-center px-3 py-2 font-medium">Điểm</th>
                  <th className="text-center px-3 py-2 font-medium">Hạn</th>
                  <th className="text-center px-3 py-2 font-medium">Sửa</th>
                  <th className="text-center px-3 py-2 font-medium">Nhắc</th>
                  <th className="text-center px-3 py-2 font-medium">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-100">
                {tasks.map(t => {
                  const overdue = t.status !== 'done' && new Date(t.deadline) < now;
                  const classified = t.classification !== 'thuong';
                  return (
                    <tr key={t._id} className={`hover:bg-navy-50/50 ${classified ? 'bg-crimson-50/30' : ''}`}>
                      <td className="px-4 py-2 font-mono text-[11px] text-navy-600 whitespace-nowrap">
                        {t.code || '—'}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-1.5">
                          {classified && <Lock size={12} className="text-crimson-600 shrink-0" />}
                          <span className={`truncate ${t.is_redacted ? 'italic text-navy-400' : 'text-navy-800'}`}>
                            {t.title}
                          </span>
                        </div>
                        {classified && (
                          <span className={`inline-block mt-0.5 px-1.5 py-0 text-[9px] font-bold tracking-wide rounded-sm border ${CLASSIFICATION_COLORS[t.classification]}`}>
                            {CLASSIFICATION_LABELS[t.classification]}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-navy-600 text-xs">{PRODUCT_LABELS[t.product] ?? t.product}</td>
                      <td className="px-3 py-2 text-center tabular font-medium text-navy-700">{t.kpi_point}</td>
                      <td className={`px-3 py-2 text-center text-xs tabular whitespace-nowrap ${overdue ? 'text-crimson-700 font-medium' : 'text-navy-600'}`}>
                        {overdue && <AlertTriangle size={11} className="inline mr-0.5" />}
                        {new Date(t.deadline).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="px-3 py-2 text-center tabular">
                        {t.revision_count > 0
                          ? <span className="text-gold-700 font-medium">{t.revision_count}</span>
                          : <span className="text-navy-300">0</span>}
                      </td>
                      <td className="px-3 py-2 text-center tabular">
                        {t.reminder_count > 0
                          ? <span className="text-crimson-700 font-medium">{t.reminder_count}</span>
                          : <span className="text-navy-300">0</span>}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span className={`px-2 py-0.5 text-[11px] rounded-sm ${TASK_STATUS_COLORS[t.status]}`}>
                          {TASK_STATUS_LABELS[t.status]}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-4 text-[11px] text-navy-400">
        <span className="inline-flex items-center gap-1"><CheckCircle2 size={11} /> Tỷ lệ hoàn thành tính trên số nhiệm vụ được giao trong kỳ</span>
        <span className="inline-flex items-center gap-1"><FileEdit size={11} /> Mỗi lần sửa làm giảm mức điểm chất lượng (B)</span>
        <span className="inline-flex items-center gap-1"><Bell size={11} /> Mỗi lần nhắc nhở làm giảm mức điểm tiến độ (C)</span>
        <span className="inline-flex items-center gap-1"><Clock size={11} /> Định mức điểm do đơn vị giao cho từng cán bộ</span>
      </div>
    </div>
  );
};

export default EmployeeDetail;
