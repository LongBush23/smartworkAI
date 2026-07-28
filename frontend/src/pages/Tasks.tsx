import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Plus, Bell, FileEdit, Trash2, ListChecks, AlertTriangle } from 'lucide-react';
import api from '../lib/api';
import { taskApi, PRODUCT_LABELS, TASK_STATUS_LABELS, TASK_STATUS_COLORS } from '../lib/task-api';
import type { Task } from '../lib/task-api';
import { qualityTierFromRevisions, timelineTierFromReminders, QUALITY_PERCENT, TIMELINE_PERCENT } from '../lib/kpi-api';
import { TaskModal } from '../components/TaskModal';

const Tasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [catalogItems, setCatalogItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState<any>(null);
  const [modalTask, setModalTask] = useState<Task | null | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState('');

  const now = new Date();
  const [period, setPeriod] = useState({ month: now.getMonth() + 1, year: now.getFullYear() });

  useEffect(() => { fetchData(); }, [period.month, period.year, statusFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const meRes = await api.get('/auth/me');
      setMe(meRes.data);

      const taskList = await taskApi.list({
        period_month: period.month,
        period_year: period.year,
        status: statusFilter || undefined,
      });
      setTasks(taskList);

      if (['leader', 'director', 'admin'].includes(meRes.data.role)) {
        const [empRes, catRes] = await Promise.all([
          api.get('/employees/').catch(() => ({ data: [] })),
          api.get('/kpi/catalog', { params: { department_id: meRes.data.department_id } }).catch(() => ({ data: [] })),
        ]);
        setUsers(empRes.data);
        setCatalogItems((catRes.data || []).flatMap((c: any) => c.items || []));
      }
    } catch (error) {
      console.error('Không tải được danh sách nhiệm vụ', error);
    } finally {
      setLoading(false);
    }
  };

  const isLeaderPlus = ['leader', 'director', 'admin'].includes(me?.role);

  const handleRemind = async (task: Task) => {
    try {
      const res = await taskApi.remind(task._id);
      toast.success(`Đã ghi nhận nhắc nhở lần ${res.reminder_count}`);
      fetchData();
    } catch { toast.error('Không ghi nhận được nhắc nhở'); }
  };

  const handleRevision = async (task: Task) => {
    try {
      const res = await taskApi.requestRevision(task._id);
      toast.success(`Đã ghi nhận yêu cầu chỉnh sửa lần ${res.revision_count}`);
      fetchData();
    } catch { toast.error('Không ghi nhận được yêu cầu chỉnh sửa'); }
  };

  const handleSave = async (data: Partial<Task>) => {
    try {
      if (modalTask?._id) {
        await taskApi.update(modalTask._id, data);
        toast.success('Đã cập nhật nhiệm vụ');
      } else {
        await taskApi.create({ ...data, period_month: period.month, period_year: period.year });
        toast.success('Đã giao nhiệm vụ mới');
      }
      setModalTask(undefined);
      fetchData();
    } catch { toast.error('Không lưu được nhiệm vụ'); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Xoá nhiệm vụ công tác này?')) return;
    try {
      await taskApi.remove(id);
      toast.success('Đã xoá nhiệm vụ');
      setModalTask(undefined);
      fetchData();
    } catch { toast.error('Không xoá được nhiệm vụ'); }
  };

  // Tổng hợp điểm A/B/C dự kiến của kỳ theo công thức tài liệu
  const totals = tasks.reduce((acc, t) => {
    acc.assigned += t.kpi_point * (t.quantity_assigned || 1);
    if (t.status === 'done') {
      const completed = t.kpi_point * (t.quantity_completed || 0);
      acc.completed += completed;
      acc.quality += completed * QUALITY_PERCENT[qualityTierFromRevisions(t.revision_count)];
      acc.timeline += completed * TIMELINE_PERCENT[timelineTierFromReminders(t.reminder_count)];
    }
    return acc;
  }, { assigned: 0, completed: 0, quality: 0, timeline: 0 });

  const pct = (v: number) => totals.assigned > 0 ? (v / totals.assigned * 100).toFixed(1) + '%' : '–';

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3 justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <ListChecks className="h-6 w-6 text-blue-600" />
          Nhiệm vụ công tác
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            <option value="">Tất cả trạng thái</option>
            {Object.entries(TASK_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select
            value={period.month}
            onChange={e => setPeriod({ ...period, month: parseInt(e.target.value) })}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            {[...Array(12)].map((_, i) => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <select
            value={period.year}
            onChange={e => setPeriod({ ...period, year: parseInt(e.target.value) })}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            {[...Array(5)].map((_, i) => {
              const y = now.getFullYear() - 2 + i;
              return <option key={y} value={y}>Năm {y}</option>;
            })}
          </select>
          {isLeaderPlus && (
            <button
              onClick={() => setModalTask(null)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              <Plus size={18} /> Giao nhiệm vụ
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500">Tổng điểm được giao</p>
          <p className="text-2xl font-bold text-gray-800 mt-1">{totals.assigned}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500">Điểm số lượng (A)</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">{pct(totals.completed)}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500">Điểm chất lượng (B)</p>
          <p className="text-2xl font-bold text-indigo-600 mt-1">{pct(totals.quality)}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500">Điểm tiến độ (C)</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{pct(totals.timeline)}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {tasks.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            Chưa có nhiệm vụ công tác nào trong tháng {period.month}/{period.year}.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-600">
                  <th className="p-3 font-medium">Nội dung nhiệm vụ</th>
                  <th className="p-3 font-medium">Sản phẩm</th>
                  <th className="p-3 font-medium text-center">Điểm</th>
                  <th className="p-3 font-medium text-center">SL giao / HT</th>
                  <th className="p-3 font-medium">Cán bộ thực hiện</th>
                  <th className="p-3 font-medium text-center">Hạn hoàn thành</th>
                  <th className="p-3 font-medium text-center">Sửa (B)</th>
                  <th className="p-3 font-medium text-center">Nhắc (C)</th>
                  <th className="p-3 font-medium text-center">Trạng thái</th>
                  <th className="p-3 font-medium text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tasks.map(t => {
                  const overdue = t.status !== 'done' && new Date(t.deadline) < now;
                  return (
                    <tr key={t._id} className="hover:bg-gray-50">
                      <td className="p-3">
                        <p className="font-medium text-gray-800">{t.title}</p>
                        {t.description && <p className="text-xs text-gray-500 line-clamp-1 mt-0.5">{t.description}</p>}
                      </td>
                      <td className="p-3 text-gray-600">{PRODUCT_LABELS[t.product] ?? t.product}</td>
                      <td className="p-3 text-center font-semibold text-blue-700">{t.kpi_point}</td>
                      <td className="p-3 text-center text-gray-700">
                        {t.quantity_assigned} / <span className="font-medium">{t.quantity_completed}</span>
                      </td>
                      <td className="p-3 text-gray-700">{t.assignee_name || <span className="text-gray-400">Chưa giao</span>}</td>
                      <td className={`p-3 text-center ${overdue ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                        <span className="inline-flex items-center gap-1">
                          {overdue && <AlertTriangle size={13} />}
                          {new Date(t.deadline).toLocaleDateString('vi-VN')}
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${t.revision_count === 0 ? 'bg-green-50 text-green-700' : t.revision_count <= 4 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'}`}>
                          {t.revision_count} lần
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${t.reminder_count === 0 ? 'bg-green-50 text-green-700' : t.reminder_count <= 2 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'}`}>
                          {t.reminder_count} lần
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${TASK_STATUS_COLORS[t.status]}`}>
                          {TASK_STATUS_LABELS[t.status]}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center justify-center gap-1">
                          {isLeaderPlus && t.status !== 'done' && (
                            <>
                              <button
                                onClick={() => handleRemind(t)}
                                title="Nhắc nhở tiến độ"
                                className="p-1.5 text-amber-600 hover:bg-amber-50 rounded"
                              >
                                <Bell size={16} />
                              </button>
                              <button
                                onClick={() => handleRevision(t)}
                                title="Yêu cầu hoàn thiện, chỉnh sửa"
                                className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded"
                              >
                                <FileEdit size={16} />
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => setModalTask(t)}
                            className="px-2 py-1 text-xs text-blue-700 hover:bg-blue-50 rounded font-medium"
                          >
                            Chi tiết
                          </button>
                          {isLeaderPlus && (
                            <button
                              onClick={() => handleDelete(t._id)}
                              title="Xoá nhiệm vụ"
                              className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalTask !== undefined && (
        <TaskModal
          task={modalTask}
          users={users}
          catalogItems={catalogItems}
          canEdit={isLeaderPlus}
          onClose={() => setModalTask(undefined)}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default Tasks;
