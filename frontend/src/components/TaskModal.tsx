import { useState, useEffect } from 'react';
import { X, Send, MessageSquare } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../lib/api';
import { PRODUCT_LABELS, TASK_STATUS_LABELS } from '../lib/task-api';
import type { Task, TaskProduct, TaskStatus } from '../lib/task-api';
import {
  qualityTierFromRevisions, timelineTierFromReminders,
  QUALITY_PERCENT, TIMELINE_PERCENT,
} from '../lib/kpi-api';

interface Props {
  /** null = tạo mới, Task = xem/sửa */
  task: Task | null;
  users: any[];
  catalogItems: any[];
  canEdit: boolean;
  onClose: () => void;
  onSave: (data: Partial<Task>) => void;
}

const emptyForm = {
  title: '',
  description: '',
  catalog_item_id: '',
  product: 'bao_cao' as TaskProduct,
  kpi_point: 50,
  quantity_assigned: 1,
  quantity_completed: 0,
  assigned_to: '',
  status: 'assigned' as TaskStatus,
  deadline: new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10),
};

export const TaskModal = ({ task, users, catalogItems, canEdit, onClose, onSave }: Props) => {
  const [tab, setTab] = useState<'details' | 'comments'>('details');
  const [form, setForm] = useState(emptyForm);
  const [comments, setComments] = useState<any[]>([]);
  const [newComment, setNewComment] = useState('');

  useEffect(() => {
    if (task) {
      setForm({
        title: task.title ?? '',
        description: task.description ?? '',
        catalog_item_id: task.catalog_item_id ?? '',
        product: task.product ?? 'bao_cao',
        kpi_point: task.kpi_point ?? 0,
        quantity_assigned: task.quantity_assigned ?? 1,
        quantity_completed: task.quantity_completed ?? 0,
        assigned_to: task.assigned_to ?? '',
        status: task.status ?? 'assigned',
        deadline: task.deadline ? task.deadline.slice(0, 10) : emptyForm.deadline,
      });
      api.get(`/tasks/${task._id}/comments`)
        .then(res => setComments(res.data))
        .catch(() => setComments([]));
    } else {
      setForm(emptyForm);
      setComments([]);
    }
  }, [task]);

  // Chọn mục trong Danh mục nhiệm vụ thì tự điền điểm theo khung đã phê duyệt
  const handlePickCatalogItem = (itemId: string) => {
    const item = catalogItems.find(i => i.id === itemId);
    setForm(f => ({
      ...f,
      catalog_item_id: itemId,
      ...(item ? { title: f.title || item.task_name, kpi_point: item.kpi_point } : {}),
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error('Chưa nhập nội dung nhiệm vụ'); return; }
    if (form.quantity_completed > form.quantity_assigned) {
      toast.error('Số lượng hoàn thành không được lớn hơn số lượng được giao');
      return;
    }
    onSave({
      ...form,
      assigned_to: form.assigned_to || undefined,
      catalog_item_id: form.catalog_item_id || undefined,
      deadline: new Date(form.deadline).toISOString(),
    });
  };

  const handleAddComment = async () => {
    if (!task || !newComment.trim()) return;
    try {
      await api.post(`/tasks/${task._id}/comments`, { content: newComment });
      setNewComment('');
      const res = await api.get(`/tasks/${task._id}/comments`);
      setComments(res.data);
    } catch { toast.error('Không gửi được ý kiến'); }
  };

  // Mức điểm B, C suy ra từ số lần sửa / nhắc nhở
  const qTier = qualityTierFromRevisions(form.quantity_completed > 0 ? (task?.revision_count ?? 0) : 0);
  const tTier = timelineTierFromReminders(task?.reminder_count ?? 0);
  const assignedPoints = form.kpi_point * form.quantity_assigned;
  const completedPoints = form.kpi_point * form.quantity_completed;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 h-14 border-b border-gray-200 shrink-0">
          <h2 className="font-semibold text-gray-800">
            {task ? 'Chi tiết nhiệm vụ công tác' : 'Giao nhiệm vụ công tác'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={22} /></button>
        </div>

        {task && (
          <div className="flex border-b border-gray-200 px-4 shrink-0">
            <button
              onClick={() => setTab('details')}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 ${tab === 'details' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500'}`}
            >
              Thông tin
            </button>
            <button
              onClick={() => setTab('comments')}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 flex items-center gap-2 ${tab === 'comments' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500'}`}
            >
              <MessageSquare size={15} /> Ý kiến ({comments.length})
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6">
          {tab === 'details' ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {catalogItems.length > 0 && canEdit && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Chọn từ Danh mục nhiệm vụ công tác
                  </label>
                  <select
                    value={form.catalog_item_id}
                    onChange={e => handlePickCatalogItem(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">— Nhiệm vụ ngoài Danh mục (phát sinh) —</option>
                    {catalogItems.map(i => (
                      <option key={i.id} value={i.id}>
                        {i.task_name} · Nhóm {i.complexity_group} · {i.kpi_point} điểm
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Nhiệm vụ phát sinh ngoài Khung Danh mục do lãnh đạo trực tiếp giao xác định nhóm và số điểm.
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nội dung nhiệm vụ *</label>
                <input
                  required disabled={!canEdit}
                  value={form.title}
                  onChange={e => setForm({ ...form, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Diễn giải</label>
                <textarea
                  disabled={!canEdit} rows={2}
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-50"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sản phẩm</label>
                  <select
                    disabled={!canEdit}
                    value={form.product}
                    onChange={e => setForm({ ...form, product: e.target.value as TaskProduct })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-50"
                  >
                    {Object.entries(PRODUCT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Điểm/sản phẩm</label>
                  <input
                    type="number" min={0} max={100} disabled={!canEdit}
                    value={form.kpi_point}
                    onChange={e => setForm({ ...form, kpi_point: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">SL được giao</label>
                  <input
                    type="number" min={0} disabled={!canEdit}
                    value={form.quantity_assigned}
                    onChange={e => setForm({ ...form, quantity_assigned: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">SL hoàn thành</label>
                  <input
                    type="number" min={0}
                    value={form.quantity_completed}
                    onChange={e => setForm({ ...form, quantity_completed: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cán bộ thực hiện</label>
                  <select
                    disabled={!canEdit}
                    value={form.assigned_to}
                    onChange={e => setForm({ ...form, assigned_to: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-50"
                  >
                    <option value="">— Chưa giao —</option>
                    {users.map(u => <option key={u._id} value={u._id}>{u.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Hạn hoàn thành</label>
                  <input
                    type="date" disabled={!canEdit}
                    value={form.deadline}
                    onChange={e => setForm({ ...form, deadline: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Trạng thái</label>
                  <select
                    value={form.status}
                    onChange={e => setForm({ ...form, status: e.target.value as TaskStatus })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    {Object.entries(TASK_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
              </div>

              {/* Ảnh hưởng tới điểm KPI */}
              {task && (
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm">
                  <p className="font-medium text-blue-800 mb-2">Ảnh hưởng tới điểm KPI của kỳ</p>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-blue-700">
                    <p>Điểm được giao:</p><p className="font-semibold">{assignedPoints}</p>
                    <p>Điểm số lượng hoàn thành (A):</p><p className="font-semibold">{completedPoints}</p>
                    <p>Đã chỉnh sửa {task.revision_count} lần → chất lượng (B):</p>
                    <p className="font-semibold">{(QUALITY_PERCENT[qTier] * 100).toFixed(0)}% → {(completedPoints * QUALITY_PERCENT[qTier]).toFixed(1)} điểm</p>
                    <p>Đã nhắc nhở {task.reminder_count} lần → tiến độ (C):</p>
                    <p className="font-semibold">{(TIMELINE_PERCENT[tTier] * 100).toFixed(0)}% → {(completedPoints * TIMELINE_PERCENT[tTier]).toFixed(1)} điểm</p>
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={onClose} className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50">
                  Đóng
                </button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                  {task ? 'Lưu thay đổi' : 'Giao nhiệm vụ'}
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="space-y-3 max-h-72 overflow-y-auto">
                {comments.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-6">Chưa có ý kiến trao đổi.</p>
                ) : comments.map(c => (
                  <div key={c._id} className="bg-gray-50 border border-gray-100 rounded-lg p-3">
                    <div className="flex justify-between items-baseline mb-1">
                      <p className="text-sm font-medium text-gray-800">{c.user_name || 'Cán bộ'}</p>
                      <p className="text-xs text-gray-400">{new Date(c.created_at).toLocaleString('vi-VN')}</p>
                    </div>
                    <p className="text-sm text-gray-700">{c.content}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  value={newComment}
                  onChange={e => setNewComment(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddComment(); } }}
                  placeholder="Nhập ý kiến trao đổi..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
                <button onClick={handleAddComment} className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <Send size={17} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
