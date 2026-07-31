import { useState, useEffect } from 'react';
import { X, Send, MessageSquare, Lock, EyeOff, ShieldAlert } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../lib/api';
import {
  PRODUCT_LABELS, TASK_STATUS_LABELS, TASK_TYPE_LABELS,
  CLASSIFICATION_LABELS, CLASSIFICATION_COLORS, CLASSIFICATION_RANK,
} from '../lib/task-api';
import type { Task, TaskProduct, TaskStatus, TaskType, Classification } from '../lib/task-api';
import {
  qualityTierFromRevisions, timelineTierFromReminders,
  QUALITY_PERCENT, TIMELINE_PERCENT,
} from '../lib/kpi-api';

interface Props {
  /** null = giao nhiệm vụ mới, Task = xem/sửa */
  task: Task | null;
  users: any[];
  catalogItems: any[];
  canEdit: boolean;
  currentUser?: any;
  onClose: () => void;
  onSave: (data: Partial<Task>) => void;
}

const emptyForm = {
  title: '',
  description: '',
  task_type: 'thuong_xuyen' as TaskType,
  classification: 'thuong' as Classification,
  file_reference: '',
  file_location: '',
  catalog_item_id: '',
  complexity_group: undefined as number | undefined,
  product: 'bao_cao' as TaskProduct,
  kpi_point: 50,
  quantity_assigned: 1,
  quantity_completed: 0,
  assigned_to: '',
  assigned_basis: '',
  status: 'assigned' as TaskStatus,
  deadline: new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10),
};

const label = 'block text-[11px] font-medium text-navy-600 mb-1';
const input = 'w-full px-2.5 py-1.5 border border-navy-200 rounded-sm text-sm disabled:bg-navy-50 disabled:text-navy-500';

export const TaskModal = ({ task, users, catalogItems, canEdit, currentUser, onClose, onSave }: Props) => {
  const [tab, setTab] = useState<'details' | 'comments'>('details');
  const [form, setForm] = useState(emptyForm);
  const [comments, setComments] = useState<any[]>([]);
  const [newComment, setNewComment] = useState('');

  const myClearance = currentUser?.clearance_level ?? 0;

  useEffect(() => {
    if (task) {
      setForm({
        title: task.title ?? '',
        description: task.description ?? '',
        task_type: task.task_type ?? 'thuong_xuyen',
        classification: task.classification ?? 'thuong',
        file_reference: task.file_reference ?? '',
        file_location: task.file_location ?? '',
        catalog_item_id: task.catalog_item_id ?? '',
        complexity_group: task.complexity_group,
        product: task.product ?? 'bao_cao',
        kpi_point: task.kpi_point ?? 0,
        quantity_assigned: task.quantity_assigned ?? 1,
        quantity_completed: task.quantity_completed ?? 0,
        assigned_to: task.assigned_to ?? '',
        assigned_basis: task.assigned_basis ?? '',
        status: task.status ?? 'assigned',
        deadline: task.deadline ? task.deadline.slice(0, 10) : emptyForm.deadline,
      });
      api.get(`/tasks/${task._id}/comments`).then(r => setComments(r.data)).catch(() => setComments([]));
    } else {
      setForm(emptyForm);
      setComments([]);
    }
  }, [task]);

  const isClassified = form.classification !== 'thuong';

  const handlePickCatalogItem = (itemId: string) => {
    const item = catalogItems.find(i => i.id === itemId);
    setForm(f => ({
      ...f,
      catalog_item_id: itemId,
      ...(item ? {
        title: f.title || item.task_name,
        kpi_point: item.kpi_point,
        complexity_group: item.complexity_group,
      } : {}),
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error('Chưa nhập nội dung nhiệm vụ'); return; }
    if (form.quantity_completed > form.quantity_assigned) {
      toast.error('Số lượng hoàn thành không được lớn hơn số lượng được giao');
      return;
    }
    if (isClassified && form.description.trim()) {
      toast.error('Nhiệm vụ có độ mật không được lưu nội dung diễn giải trong hệ thống');
      return;
    }
    onSave({
      ...form,
      description: isClassified ? undefined : form.description || undefined,
      file_reference: isClassified ? form.file_reference || undefined : undefined,
      file_location: isClassified ? form.file_location || undefined : undefined,
      complexity_group: form.complexity_group as 1 | 2 | 3 | undefined,
      assigned_to: form.assigned_to || undefined,
      catalog_item_id: form.catalog_item_id || undefined,
      assigned_basis: form.assigned_basis || undefined,
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

  // Điểm và mức B, C
  const assignedPoints = form.kpi_point * form.quantity_assigned;
  const completedPoints = form.kpi_point * form.quantity_completed;
  const maxPoints = Math.round(assignedPoints * 1.2);
  const qTier = qualityTierFromRevisions(task?.revision_count ?? 0);
  const tTier = timelineTierFromReminders(task?.reminder_count ?? 0);

  const daysLeft = Math.ceil((+new Date(form.deadline) - Date.now()) / 864e5);

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-sm shadow-xl w-full max-w-3xl max-h-[92vh] flex flex-col">
        {/* Tiêu đề */}
        <div className="flex items-center justify-between px-5 h-14 bg-navy-700 text-white shrink-0">
          <div className="min-w-0">
            <h2 className="font-semibold text-sm">
              {task ? 'Chi tiết nhiệm vụ công tác' : 'Giao nhiệm vụ công tác'}
            </h2>
            {task?.code && <p className="text-[11px] text-navy-200 font-mono">{task.code}</p>}
          </div>
          <div className="flex items-center gap-2">
            {isClassified && (
              <span className={`px-2 py-0.5 text-[10px] font-bold tracking-wider rounded-sm border ${CLASSIFICATION_COLORS[form.classification]}`}>
                <Lock size={10} className="inline mr-1" />
                {CLASSIFICATION_LABELS[form.classification]}
              </span>
            )}
            <button onClick={onClose} className="text-navy-200 hover:text-white"><X size={20} /></button>
          </div>
        </div>

        {task?.is_redacted && (
          <div className="classified-hatch px-5 py-3 border-b border-crimson-200 flex items-start gap-2">
            <EyeOff size={16} className="text-crimson-700 shrink-0 mt-0.5" />
            <div className="text-xs text-crimson-900">
              <p className="font-semibold">Thông tin đã được che theo cấp độ tiếp cận</p>
              <p className="mt-0.5">
                Cấp độ tiếp cận của bạn không đủ để xem nội dung và số hiệu hồ sơ của nhiệm vụ này.
                Máy chủ đã loại bỏ các trường đó khỏi dữ liệu trả về. Lượt truy cập này đã được ghi nhật ký.
              </p>
            </div>
          </div>
        )}

        {task && (
          <div className="flex border-b border-navy-200 px-4 shrink-0 bg-navy-50">
            <button onClick={() => setTab('details')}
              className={`px-4 py-2 text-xs font-medium border-b-2 ${tab === 'details' ? 'border-navy-600 text-navy-800' : 'border-transparent text-navy-500'}`}>
              Thông tin nhiệm vụ
            </button>
            <button onClick={() => setTab('comments')}
              className={`px-4 py-2 text-xs font-medium border-b-2 flex items-center gap-1.5 ${tab === 'comments' ? 'border-navy-600 text-navy-800' : 'border-transparent text-navy-500'}`}>
              <MessageSquare size={13} /> Ý kiến ({comments.length})
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-5 custom-scrollbar">
          {tab === 'details' ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Phân loại */}
              <fieldset className="border border-navy-200 rounded-sm p-3">
                <legend className="section-label px-1">Phân loại nhiệm vụ</legend>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className={label}>Loại nhiệm vụ</label>
                    <select disabled={!canEdit} value={form.task_type}
                      onChange={e => setForm({ ...form, task_type: e.target.value as TaskType })}
                      className={input}>
                      {Object.entries(TASK_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={label}>Độ mật</label>
                    <select disabled={!canEdit} value={form.classification}
                      onChange={e => setForm({ ...form, classification: e.target.value as Classification })}
                      className={input}>
                      {Object.entries(CLASSIFICATION_LABELS).map(([k, v]) => (
                        <option key={k} value={k} disabled={CLASSIFICATION_RANK[k as Classification] > myClearance}>
                          {v}{CLASSIFICATION_RANK[k as Classification] > myClearance ? ' — vượt cấp độ tiếp cận' : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {isClassified && (
                  <div className="mt-3 bg-crimson-50 border border-crimson-200 rounded-sm p-3">
                    <p className="text-[11px] text-crimson-900 flex items-start gap-1.5 mb-3">
                      <ShieldAlert size={13} className="shrink-0 mt-0.5" />
                      <span>
                        Hệ thống <strong>không lưu nội dung</strong> của nhiệm vụ có độ mật.
                        Chỉ ghi mã hiệu, tên gọi quy ước, điểm, thời hạn và số hiệu hồ sơ gốc.
                      </span>
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className={label}>Số hiệu hồ sơ gốc</label>
                        <input disabled={!canEdit} value={form.file_reference}
                          placeholder="VD: Số 148/HS-PA03"
                          onChange={e => setForm({ ...form, file_reference: e.target.value })}
                          className={input} />
                      </div>
                      <div>
                        <label className={label}>Nơi lưu hồ sơ</label>
                        <input disabled={!canEdit} value={form.file_location}
                          placeholder="VD: Bộ phận cơ yếu đơn vị"
                          onChange={e => setForm({ ...form, file_location: e.target.value })}
                          className={input} />
                      </div>
                    </div>
                  </div>
                )}
              </fieldset>

              {/* Nội dung */}
              <fieldset className="border border-navy-200 rounded-sm p-3">
                <legend className="section-label px-1">Nội dung nhiệm vụ</legend>

                {catalogItems.length > 0 && canEdit && (
                  <div className="mb-3">
                    <label className={label}>Chọn từ Danh mục nhiệm vụ công tác</label>
                    <select value={form.catalog_item_id}
                      onChange={e => handlePickCatalogItem(e.target.value)} className={input}>
                      <option value="">— Nhiệm vụ phát sinh ngoài Danh mục —</option>
                      {catalogItems.map(i => (
                        <option key={i.id} value={i.id}>
                          {i.task_name} · Nhóm {i.complexity_group} · {i.kpi_point} điểm
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="mb-3">
                  <label className={label}>
                    {isClassified ? 'Tên gọi quy ước *' : 'Nội dung nhiệm vụ *'}
                  </label>
                  <input required disabled={!canEdit} value={form.title}
                    placeholder={isClassified ? 'VD: Nhiệm vụ chuyên đề A1' : ''}
                    onChange={e => setForm({ ...form, title: e.target.value })} className={input} />
                </div>

                {!isClassified && (
                  <div className="mb-3">
                    <label className={label}>Diễn giải</label>
                    <textarea disabled={!canEdit} rows={2} value={form.description}
                      onChange={e => setForm({ ...form, description: e.target.value })} className={input} />
                  </div>
                )}

                <div>
                  <label className={label}>Căn cứ giao nhiệm vụ</label>
                  <input disabled={!canEdit} value={form.assigned_basis}
                    placeholder="VD: Kế hoạch số 12/KH-BCA ngày 03/4/2026"
                    onChange={e => setForm({ ...form, assigned_basis: e.target.value })} className={input} />
                </div>
              </fieldset>

              {/* Sản phẩm và điểm */}
              <fieldset className="border border-navy-200 rounded-sm p-3">
                <legend className="section-label px-1">Sản phẩm và điểm</legend>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  <div>
                    <label className={label}>Sản phẩm</label>
                    <select disabled={!canEdit} value={form.product}
                      onChange={e => setForm({ ...form, product: e.target.value as TaskProduct })} className={input}>
                      {Object.entries(PRODUCT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={label}>Nhóm</label>
                    <select disabled={!canEdit} value={form.complexity_group ?? ''}
                      onChange={e => setForm({ ...form, complexity_group: e.target.value ? parseInt(e.target.value) : undefined })}
                      className={input}>
                      <option value="">—</option>
                      <option value={1}>Nhóm 1</option>
                      <option value={2}>Nhóm 2</option>
                      <option value={3}>Nhóm 3</option>
                    </select>
                  </div>
                  <div>
                    <label className={label}>Điểm/SP</label>
                    <input type="number" min={0} max={100} disabled={!canEdit} value={form.kpi_point}
                      onChange={e => setForm({ ...form, kpi_point: parseInt(e.target.value) || 0 })} className={input} />
                  </div>
                  <div>
                    <label className={label}>SL giao</label>
                    <input type="number" min={0} disabled={!canEdit} value={form.quantity_assigned}
                      onChange={e => setForm({ ...form, quantity_assigned: parseInt(e.target.value) || 0 })} className={input} />
                  </div>
                  <div>
                    <label className={label}>SL hoàn thành</label>
                    <input type="number" min={0} value={form.quantity_completed}
                      onChange={e => setForm({ ...form, quantity_completed: parseInt(e.target.value) || 0 })} className={input} />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 mt-3 pt-3 border-t border-navy-100 text-center">
                  <div>
                    <p className="section-label">Điểm được giao</p>
                    <p className="text-xl font-bold text-navy-800 tabular">{assignedPoints}</p>
                  </div>
                  <div>
                    <p className="section-label">Điểm tối đa đạt được</p>
                    <p className="text-xl font-bold text-gold-600 tabular">{maxPoints}</p>
                    <p className="text-[9px] text-navy-400">khi vượt mức 120%</p>
                  </div>
                  <div>
                    <p className="section-label">Điểm đã hoàn thành</p>
                    <p className="text-xl font-bold text-emerald-700 tabular">{completedPoints}</p>
                  </div>
                </div>
              </fieldset>

              {/* Giao việc và tiến độ */}
              <fieldset className="border border-navy-200 rounded-sm p-3">
                <legend className="section-label px-1">Giao việc và tiến độ</legend>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className={label}>Cán bộ thực hiện</label>
                    <select disabled={!canEdit} value={form.assigned_to}
                      onChange={e => setForm({ ...form, assigned_to: e.target.value })} className={input}>
                      <option value="">— Chưa giao —</option>
                      {users.map(u => <option key={u._id} value={u._id}>{u.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={label}>Hạn hoàn thành</label>
                    <input type="date" disabled={!canEdit} value={form.deadline}
                      onChange={e => setForm({ ...form, deadline: e.target.value })} className={input} />
                    {task && (
                      <p className={`text-[10px] mt-0.5 ${daysLeft < 0 ? 'text-crimson-700 font-medium' : 'text-navy-400'}`}>
                        {form.status === 'done' ? 'Đã hoàn thành'
                          : daysLeft < 0 ? `Trễ ${Math.abs(daysLeft)} ngày`
                          : `Còn ${daysLeft} ngày`}
                      </p>
                    )}
                  </div>
                  <div>
                    <label className={label}>Trạng thái</label>
                    <select value={form.status}
                      onChange={e => setForm({ ...form, status: e.target.value as TaskStatus })} className={input}>
                      {Object.entries(TASK_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                  </div>
                </div>

                {task && (
                  <div className="mt-3 pt-3 border-t border-navy-100 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="bg-navy-50 rounded-sm p-2.5">
                      <p className="text-[11px] text-navy-600">
                        Đã chỉnh sửa <strong className="text-navy-900">{task.revision_count}</strong> lần
                        → mức chất lượng (B)
                      </p>
                      <p className="text-lg font-bold text-gold-600 tabular">
                        {(QUALITY_PERCENT[qTier] * 100).toFixed(0)}%
                        <span className="text-xs font-normal text-navy-500 ml-1.5">
                          = {(completedPoints * QUALITY_PERCENT[qTier]).toFixed(1)} điểm
                        </span>
                      </p>
                    </div>
                    <div className="bg-navy-50 rounded-sm p-2.5">
                      <p className="text-[11px] text-navy-600">
                        Đã nhắc nhở <strong className="text-navy-900">{task.reminder_count}</strong> lần
                        → mức tiến độ (C)
                      </p>
                      <p className="text-lg font-bold text-emerald-700 tabular">
                        {(TIMELINE_PERCENT[tTier] * 100).toFixed(0)}%
                        <span className="text-xs font-normal text-navy-500 ml-1.5">
                          = {(completedPoints * TIMELINE_PERCENT[tTier]).toFixed(1)} điểm
                        </span>
                      </p>
                    </div>
                  </div>
                )}

                {task?.assigned_by_name && (
                  <p className="text-[11px] text-navy-500 mt-3">
                    Người giao: <strong className="text-navy-700">{task.assigned_by_name}</strong>
                    {task.assigned_at && ` · ${new Date(task.assigned_at).toLocaleDateString('vi-VN')}`}
                  </p>
                )}
              </fieldset>

              <div className="flex justify-end gap-2">
                <button type="button" onClick={onClose}
                  className="px-4 py-1.5 border border-navy-300 rounded-sm text-sm text-navy-700 hover:bg-navy-50">
                  Đóng
                </button>
                {canEdit && !task?.is_redacted && (
                  <button type="submit"
                    className="px-4 py-1.5 bg-navy-700 text-white rounded-sm text-sm hover:bg-navy-800">
                    {task ? 'Lưu thay đổi' : 'Giao nhiệm vụ'}
                  </button>
                )}
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2 max-h-72 overflow-y-auto custom-scrollbar">
                {comments.length === 0 ? (
                  <p className="text-sm text-navy-400 text-center py-6">Chưa có ý kiến trao đổi.</p>
                ) : comments.map(c => (
                  <div key={c._id} className="bg-navy-50 border border-navy-100 rounded-sm p-2.5">
                    <div className="flex justify-between items-baseline mb-1">
                      <p className="text-xs font-medium text-navy-800">{c.user_name || 'Cán bộ'}</p>
                      <p className="text-[10px] text-navy-400">{new Date(c.created_at).toLocaleString('vi-VN')}</p>
                    </div>
                    <p className="text-sm text-navy-700">{c.content}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input value={newComment} onChange={e => setNewComment(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddComment(); } }}
                  placeholder="Nhập ý kiến trao đổi..." className={input} />
                <button onClick={handleAddComment}
                  className="px-3 py-1.5 bg-navy-700 text-white rounded-sm hover:bg-navy-800 shrink-0">
                  <Send size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
