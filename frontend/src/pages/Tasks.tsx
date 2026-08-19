import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Plus, Bell, FileEdit, Trash2, ListChecks, AlertTriangle, Lock } from 'lucide-react';
import api from '../lib/api';
import TaskTitle from '../components/TaskTitle';
import {
  taskApi, PRODUCT_LABELS, TASK_STATUS_LABELS, TASK_STATUS_COLORS,
  TASK_TYPE_LABELS, TASK_TYPE_COLORS, CLASSIFICATION_LABELS,
} from '../lib/task-api';
import type { Task } from '../lib/task-api';
import {
  qualityTierFromRevisions, timelineTierFromReminders, QUALITY_PERCENT, TIMELINE_PERCENT,
} from '../lib/kpi-api';
import { TaskModal } from '../components/TaskModal';
import { layMe } from '../lib/me';

const Tasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [catalogItems, setCatalogItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState<any>(null);
  const [modalTask, setModalTask] = useState<Task | null | undefined>(undefined);

  const [filters, setFilters] = useState({ status: '', task_type: '', classification: '' });
  const now = new Date();
  const [period, setPeriod] = useState({ month: now.getMonth() + 1, year: now.getFullYear() });

  useEffect(() => { fetchData(); }, [period.month, period.year, filters.status, filters.task_type, filters.classification]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const meRes = { data: await layMe() };
      setMe(meRes.data);

      const taskList = await taskApi.list({
        period_month: period.month,
        period_year: period.year,
        status: filters.status || undefined,
        task_type: filters.task_type || undefined,
        classification: filters.classification || undefined,
      });
      setTasks(taskList);

      if (['leader', 'director', 'admin'].includes(meRes.data.role)) {
        const [empRes, catRes] = await Promise.all([
          api.get('/employees/').catch(() => ({ data: [] })),
          api.get('/kpi/catalog', { params: { department_id: meRes.data.department_id } }).catch(() => ({ data: [] })),
        ]);
        setUsers(empRes.data);
        // Gộp mục của mọi danh mục, loại trùng id để tránh trùng khoá khi hiển thị
        const merged = new Map<string, any>();
        for (const c of catRes.data || []) {
          for (const item of c.items || []) {
            if (!merged.has(item.id)) merged.set(item.id, item);
          }
        }
        setCatalogItems([...merged.values()]);
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

  /**
   * Trả về mã nhiệm vụ đã lưu, hoặc null nếu lưu hỏng.
   *
   * Hộp nhiệm vụ cần biết kết quả để chỉ ghi nhật ký gợi ý phân công khi việc
   * giao thực sự xảy ra — ghi cả lượt lưu hỏng thì sổ đầy quyết định chưa từng có.
   */
  const handleSave = async (data: Partial<Task>): Promise<string | null> => {
    try {
      let id: string | null = modalTask?._id ?? null;
      if (modalTask?._id) {
        await taskApi.update(modalTask._id, data);
        toast.success('Đã cập nhật nhiệm vụ');
      } else {
        const moi = await taskApi.create({ ...data, period_month: period.month, period_year: period.year });
        id = moi?._id ?? null;
        toast.success('Đã giao nhiệm vụ mới');
      }
      setModalTask(undefined);
      fetchData();
      return id;
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Không lưu được nhiệm vụ');
      return null;
    }
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

  // Tổng hợp A/B/C dự kiến của kỳ theo công thức 20-HD/ĐUCA
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
  const classifiedCount = tasks.filter(t => t.classification !== 'thuong').length;

  const selectClass = 'px-2.5 py-1.5 border border-navy-200 rounded-sm text-xs bg-white text-navy-700';

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-600" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 justify-between items-start">
        <div>
          <h1 className="text-xl font-bold text-navy-900 flex items-center gap-2">
            <ListChecks className="h-5 w-5 text-navy-600" /> Nhiệm vụ công tác
          </h1>
          <p className="text-xs text-navy-500 mt-0.5">
            Kỳ tháng {period.month}/{period.year} · {tasks.length} nhiệm vụ
            {classifiedCount > 0 && (
              <span className="text-crimson-700"> · {classifiedCount} có độ mật</span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <select value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value })} className={selectClass}>
            <option value="">Mọi trạng thái</option>
            {Object.entries(TASK_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.task_type} onChange={e => setFilters({ ...filters, task_type: e.target.value })} className={selectClass}>
            <option value="">Mọi loại</option>
            {Object.entries(TASK_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.classification} onChange={e => setFilters({ ...filters, classification: e.target.value })} className={selectClass}>
            <option value="">Mọi độ mật</option>
            {Object.entries(CLASSIFICATION_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={period.month} onChange={e => setPeriod({ ...period, month: parseInt(e.target.value) })} className={selectClass}>
            {[...Array(12)].map((_, i) => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <select value={period.year} onChange={e => setPeriod({ ...period, year: parseInt(e.target.value) })} className={selectClass}>
            {[...Array(5)].map((_, i) => {
              const y = now.getFullYear() - 2 + i;
              return <option key={y} value={y}>{y}</option>;
            })}
          </select>
          {isLeaderPlus && (
            <button
              onClick={() => setModalTask(null)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 text-white rounded-sm hover:bg-navy-800 text-xs font-medium"
            >
              <Plus size={15} /> Giao nhiệm vụ
            </button>
          )}
        </div>
      </div>

      {/* Tổng hợp điểm A/B/C */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Tổng điểm được giao', value: totals.assigned.toString(), color: 'text-navy-900' },
          { label: 'Điểm số lượng (A)', value: pct(totals.completed), color: 'text-navy-700' },
          { label: 'Điểm chất lượng (B)', value: pct(totals.quality), color: 'text-gold-600' },
          { label: 'Điểm tiến độ (C)', value: pct(totals.timeline), color: 'text-emerald-700' },
        ].map(s => (
          <div key={s.label} className="bg-white border border-navy-200 rounded-sm p-3">
            <p className="section-label">{s.label}</p>
            <p className={`text-2xl font-bold tabular mt-0.5 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-navy-200 rounded-sm overflow-hidden">
        {tasks.length === 0 ? (
          <div className="p-12 text-center text-navy-400 text-sm">
            Không có nhiệm vụ nào khớp điều kiện lọc trong kỳ này.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-navy-50 border-b border-navy-200 text-navy-600 text-xs">
                  <th className="px-3 py-2 font-medium">Mã hiệu</th>
                  <th className="px-3 py-2 font-medium">Nội dung nhiệm vụ</th>
                  <th className="px-3 py-2 font-medium">Loại</th>
                  <th className="px-3 py-2 font-medium">Sản phẩm</th>
                  <th className="px-3 py-2 font-medium text-center">Điểm</th>
                  <th className="px-3 py-2 font-medium text-center">SL</th>
                  <th className="px-3 py-2 font-medium">Cán bộ thực hiện</th>
                  <th className="px-3 py-2 font-medium text-center">Hạn</th>
                  <th className="px-3 py-2 font-medium text-center">Sửa</th>
                  <th className="px-3 py-2 font-medium text-center">Nhắc</th>
                  <th className="px-3 py-2 font-medium text-center">Trạng thái</th>
                  <th className="px-3 py-2 font-medium text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-100">
                {tasks.map(t => {
                  const overdue = t.status !== 'done' && new Date(t.deadline) < now;
                  const classified = t.classification !== 'thuong';
                  const daysLeft = Math.ceil((+new Date(t.deadline) - +now) / 864e5);
                  return (
                    <tr key={t._id} className={`hover:bg-navy-50/60 ${classified ? 'bg-crimson-50/40' : ''}`}>
                      <td className="px-3 py-2 font-mono text-[11px] text-navy-600 whitespace-nowrap">
                        {t.code || '—'}
                      </td>
                      <td className="px-3 py-2 max-w-xs">
                        <TaskTitle
                          title={t.title}
                          code={t.code}
                          classification={t.classification}
                          isRedacted={t.is_redacted}
                          fileReference={t.file_reference}
                        />
                        {!classified && t.description && (
                          <p className="text-[11px] text-navy-400 truncate mt-0.5">{t.description}</p>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`px-1.5 py-0.5 text-[10px] rounded-sm border whitespace-nowrap ${TASK_TYPE_COLORS[t.task_type] ?? ''}`}>
                          {TASK_TYPE_LABELS[t.task_type] ?? t.task_type}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-navy-600 text-xs whitespace-nowrap">
                        {PRODUCT_LABELS[t.product] ?? t.product}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span className="font-semibold text-navy-800 tabular">{t.kpi_point}</span>
                        {t.complexity_group && (
                          <span className="block text-[9px] text-navy-400">N{t.complexity_group}</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-center tabular text-xs text-navy-700 whitespace-nowrap">
                        {t.quantity_completed}/{t.quantity_assigned}
                      </td>
                      <td className="px-3 py-2 text-navy-700 text-xs truncate max-w-32">
                        {t.assignee_name || <span className="text-navy-300">Chưa giao</span>}
                        {t.co_assignees?.length > 0 && (
                          <span className="block text-[10px] text-navy-400">+{t.co_assignees.length} phối hợp</span>
                        )}
                      </td>
                      <td className={`px-3 py-2 text-center text-xs tabular whitespace-nowrap ${overdue ? 'text-crimson-700 font-medium' : 'text-navy-600'}`}>
                        {overdue && <AlertTriangle size={11} className="inline mr-0.5" />}
                        {new Date(t.deadline).toLocaleDateString('vi-VN')}
                        <span className="block text-[9px] text-navy-400">
                          {t.status === 'done' ? 'đã xong'
                            : overdue ? `trễ ${Math.abs(daysLeft)} ngày`
                            : `còn ${daysLeft} ngày`}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center tabular">
                        <span className={t.revision_count === 0 ? 'text-navy-300' : t.revision_count <= 4 ? 'text-gold-700 font-medium' : 'text-crimson-700 font-medium'}>
                          {t.revision_count}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center tabular">
                        <span className={t.reminder_count === 0 ? 'text-navy-300' : t.reminder_count <= 2 ? 'text-gold-700 font-medium' : 'text-crimson-700 font-medium'}>
                          {t.reminder_count}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span className={`px-2 py-0.5 text-[11px] rounded-sm whitespace-nowrap ${TASK_STATUS_COLORS[t.status]}`}>
                          {TASK_STATUS_LABELS[t.status]}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center justify-center gap-0.5">
                          {isLeaderPlus && t.status !== 'done' && !t.is_redacted && (
                            <>
                              <button onClick={() => handleRemind(t)} title="Nhắc nhở tiến độ"
                                className="p-1 text-gold-600 hover:bg-gold-50 rounded-sm">
                                <Bell size={14} />
                              </button>
                              <button onClick={() => handleRevision(t)} title="Yêu cầu hoàn thiện, chỉnh sửa"
                                className="p-1 text-navy-600 hover:bg-navy-50 rounded-sm">
                                <FileEdit size={14} />
                              </button>
                            </>
                          )}
                          <button onClick={() => setModalTask(t)}
                            className="px-1.5 py-0.5 text-[11px] text-navy-700 hover:bg-navy-100 rounded-sm font-medium">
                            Chi tiết
                          </button>
                          {isLeaderPlus && !t.is_redacted && (
                            <button onClick={() => handleDelete(t._id)} title="Xoá nhiệm vụ"
                              className="p-1 text-crimson-500 hover:bg-crimson-50 rounded-sm">
                              <Trash2 size={14} />
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

      {classifiedCount > 0 && (
        <div className="flex items-start gap-2 text-[11px] text-navy-500 bg-crimson-50 border border-crimson-200 rounded-sm px-3 py-2">
          <Lock size={13} className="text-crimson-600 shrink-0 mt-0.5" />
          <p>
            Nhiệm vụ có độ mật chỉ lưu <strong>mã hiệu, tên gọi quy ước, điểm và thời hạn</strong> trong hệ thống.
            Nội dung nghiệp vụ được quản lý theo chế độ mật tại đơn vị theo số hiệu hồ sơ gốc.
            Mọi lượt truy cập đều được ghi nhật ký.
          </p>
        </div>
      )}

      {modalTask !== undefined && (
        <TaskModal
          task={modalTask}
          users={users}
          catalogItems={catalogItems}
          canEdit={isLeaderPlus}
          currentUser={me}
          onClose={() => setModalTask(undefined)}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default Tasks;
