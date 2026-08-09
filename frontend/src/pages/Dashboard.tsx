import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { ListChecks, Award, TrendingUp, AlertTriangle, ArrowRight, Bell, FileEdit } from 'lucide-react';
import { kpiApi, KPI_GROUP_LABELS, KPI_GROUP_COLORS } from '../lib/kpi-api';
import type { KPIEvaluation } from '../lib/kpi-api';
import { taskApi, TASK_STATUS_LABELS, TASK_STATUS_COLORS } from '../lib/task-api';
import type { Task } from '../lib/task-api';
import { EarlyWarning } from '../components/EarlyWarning';
import TaskTitle from '../components/TaskTitle';
import { layMe } from '../lib/me';

const MONTH_NAMES = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12'];

const STEP_HINT: Record<string, { label: string; cls: string; to: string }> = {
  draft:           { label: 'Bạn cần tự đánh giá (Bước 1)',        cls: 'bg-blue-50 border-blue-200 text-blue-800',     to: '/kpi/evaluate' },
  self_evaluating: { label: 'Đang chờ cơ quan thẩm định (Bước 2)',  cls: 'bg-amber-50 border-amber-200 text-amber-800',   to: '/kpi/evaluate' },
  reviewing:       { label: 'Đang chờ xác định điểm KPI (Bước 3)',  cls: 'bg-orange-50 border-orange-200 text-orange-800', to: '/kpi/evaluate' },
  approved:        { label: 'Đã xác định điểm KPI của kỳ',          cls: 'bg-green-50 border-green-200 text-green-800',   to: '/kpi/results' },
};

const Dashboard = () => {
  const [me, setMe] = useState<any>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [myEvals, setMyEvals] = useState<KPIEvaluation[]>([]);
  const [loading, setLoading] = useState(true);

  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const meRes = { data: await layMe() };
        setMe(meRes.data);

        const [taskList, evals] = await Promise.all([
          taskApi.list({ assignee_id: meRes.data._id, period_month: month, period_year: year }).catch(() => []),
          kpiApi.getEvaluations({ target_id: meRes.data._id, period_year: year }).catch(() => []),
        ]);
        setTasks(taskList);
        setMyEvals(evals);
      } catch (error) {
        console.error('Không tải được dữ liệu trang chủ', error);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [month, year]);

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  const currentEval = myEvals.find(e => e.period_month === month && e.period_type === 'monthly');
  const hint = currentEval ? STEP_HINT[currentEval.overall_status] : null;

  // Diễn biến KPI theo tháng trong năm
  const approvedMonthly = myEvals
    .filter(e => e.period_type === 'monthly' && e.overall_status === 'approved' && e.approval?.kpi_score != null)
    .sort((a, b) => (a.period_month ?? 0) - (b.period_month ?? 0));

  const trendData = approvedMonthly.map(e => ({
    name: MONTH_NAMES[(e.period_month ?? 1) - 1],
    kpi: Number(Number(e.approval.kpi_score).toFixed(1)),
  }));

  const avgKpi = approvedMonthly.length
    ? approvedMonthly.reduce((s, e) => s + Number(e.approval.kpi_score), 0) / approvedMonthly.length
    : null;

  const latest = approvedMonthly[approvedMonthly.length - 1];

  const overdue = tasks.filter(t => t.status !== 'done' && new Date(t.deadline) < now);
  const doneCount = tasks.filter(t => t.status === 'done').length;
  const totalRevisions = tasks.reduce((s, t) => s + (t.revision_count || 0), 0);
  const totalReminders = tasks.reduce((s, t) => s + (t.reminder_count || 0), 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Xin chào, {me?.name || 'đồng chí'}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {me?.position ? `${me.position} · ` : ''}Kỳ đánh giá tháng {month}/{year}
        </p>
      </div>

      {hint && (
        <Link to={hint.to} className={`flex items-center justify-between gap-3 border rounded-xl px-5 py-4 ${hint.cls} hover:brightness-[0.98] transition`}>
          <div className="flex items-center gap-3">
            <Award size={20} />
            <span className="font-medium text-sm">{hint.label}</span>
          </div>
          <ArrowRight size={18} />
        </Link>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500">Nhiệm vụ tháng này</p>
              <p className="text-2xl font-bold text-gray-800 mt-1">{doneCount}/{tasks.length}</p>
              <p className="text-xs text-gray-400 mt-0.5">đã hoàn thành</p>
            </div>
            <div className="p-2.5 bg-blue-50 rounded-lg"><ListChecks className="h-5 w-5 text-blue-600" /></div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500">Quá hạn</p>
              <p className={`text-2xl font-bold mt-1 ${overdue.length > 0 ? 'text-red-600' : 'text-gray-800'}`}>{overdue.length}</p>
              <p className="text-xs text-gray-400 mt-0.5">nhiệm vụ</p>
            </div>
            <div className="p-2.5 bg-red-50 rounded-lg"><AlertTriangle className="h-5 w-5 text-red-600" /></div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500">KPI kỳ gần nhất</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">
                {latest ? Number(latest.approval.kpi_score).toFixed(1) : '–'}
              </p>
              {latest && (
                <span className={`inline-block mt-1 px-2 py-0.5 text-[10px] font-medium rounded-full border ${KPI_GROUP_COLORS[latest.approval.kpi_group] ?? ''}`}>
                  {KPI_GROUP_LABELS[latest.approval.kpi_group] ?? latest.approval.kpi_group}
                </span>
              )}
            </div>
            <div className="p-2.5 bg-indigo-50 rounded-lg"><Award className="h-5 w-5 text-indigo-600" /></div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500">KPI bình quân năm {year}</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">{avgKpi != null ? avgKpi.toFixed(1) : '–'}</p>
              <p className="text-xs text-gray-400 mt-0.5">{approvedMonthly.length} tháng đã duyệt</p>
            </div>
            <div className="p-2.5 bg-emerald-50 rounded-lg"><TrendingUp className="h-5 w-5 text-emerald-600" /></div>
          </div>
        </div>
      </div>

      {['leader', 'director', 'admin'].includes(me?.role) && (
        <EarlyWarning departmentId={me?.department_id} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Diễn biến KPI */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="font-bold text-gray-800 mb-1">Diễn biến điểm KPI năm {year}</h2>
          <p className="text-xs text-gray-500 mb-4">
            KPI quý, năm được xác định bằng bình quân điểm KPI hằng tháng.
          </p>
          {trendData.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-16">Chưa có kỳ nào được phê duyệt trong năm.</p>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis domain={[0, 120]} fontSize={12} />
                  <Tooltip formatter={(v) => [`${v} điểm`, 'KPI']} />
                  <Line type="monotone" dataKey="kpi" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Chất lượng & tiến độ */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="font-bold text-gray-800 mb-4">Chất lượng &amp; tiến độ tháng {month}</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
              <div className="flex items-center gap-2.5">
                <FileEdit className="h-4 w-4 text-indigo-600" />
                <span className="text-sm text-gray-700">Số lần phải chỉnh sửa</span>
              </div>
              <span className="font-bold text-indigo-700">{totalRevisions}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
              <div className="flex items-center gap-2.5">
                <Bell className="h-4 w-4 text-amber-600" />
                <span className="text-sm text-gray-700">Số lần bị nhắc nhở</span>
              </div>
              <span className="font-bold text-amber-700">{totalReminders}</span>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4 leading-relaxed">
            Mỗi lần chỉnh sửa làm giảm mức điểm chất lượng (B); mỗi lần nhắc nhở làm giảm mức điểm tiến độ (C).
          </p>
        </div>
      </div>

      {/* Nhiệm vụ gần hạn */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="font-semibold text-gray-800">Nhiệm vụ công tác của tôi</h2>
          <Link to="/tasks" className="text-sm text-blue-700 hover:underline font-medium">Xem tất cả</Link>
        </div>
        {tasks.length === 0 ? (
          <p className="p-10 text-center text-sm text-gray-500">Chưa có nhiệm vụ nào được giao trong tháng này.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {[...tasks]
              .sort((a, b) => +new Date(a.deadline) - +new Date(b.deadline))
              .slice(0, 6)
              .map(t => {
                const isOverdue = t.status !== 'done' && new Date(t.deadline) < now;
                const coDoMat = t.classification !== 'thuong';
                return (
                  <li
                    key={t._id}
                    className={`flex items-center justify-between gap-4 px-5 py-3 hover:bg-navy-50/60 ${
                      coDoMat ? 'bg-crimson-50/40' : ''
                    }`}
                  >
                    <div className="min-w-0">
                      {/* Dùng component chung để nhiệm vụ có độ mật luôn hiện ổ
                          khoá và huy hiệu — trước đây chỗ này in thẳng t.title */}
                      <TaskTitle
                        title={t.title}
                        code={t.code}
                        classification={t.classification}
                        isRedacted={t.is_redacted}
                        fileReference={t.file_reference}
                        className="text-sm"
                      />
                      <p className={`text-xs mt-0.5 ${isOverdue ? 'text-crimson-600 font-medium' : 'text-navy-500'}`}>
                        Hạn {new Date(t.deadline).toLocaleDateString('vi-VN')}
                        {isOverdue && ' · quá hạn'}
                        {' · '}{t.kpi_point} điểm
                      </p>
                    </div>
                    <span className={`shrink-0 px-2 py-1 rounded-full text-xs font-medium ${TASK_STATUS_COLORS[t.status]}`}>
                      {TASK_STATUS_LABELS[t.status]}
                    </span>
                  </li>
                );
              })}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
