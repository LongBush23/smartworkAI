import { useState, useEffect, useMemo } from 'react';
import {
  X, Send, MessageSquare, Lock, EyeOff, ShieldAlert,
  UserCheck, Info, ChevronDown, ChevronRight,
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../lib/api';
import { aiApi, NHAN_THANH_PHAN } from '../lib/ai-api';
import type { AssignmentResult } from '../lib/ai-api';
import { KhungMoHinh } from './KhungMoHinh';
import {
  PRODUCT_LABELS, TASK_STATUS_LABELS, TASK_TYPE_LABELS,
  CLASSIFICATION_LABELS, CLASSIFICATION_COLORS, CLASSIFICATION_RANK,
} from '../lib/task-api';
import type { Task, TaskProduct, TaskStatus, TaskType, Classification } from '../lib/task-api';
import {
  qualityTierFromRevisions, timelineTierFromReminders,
  QUALITY_PERCENT, TIMELINE_PERCENT,
} from '../lib/kpi-api';

// Màu 5 thành phần của điểm phù hợp. Chỉ cần phân biệt được, nên dùng thang navy
// đi từ đậm sang nhạt rồi sang vàng đồng — không dùng đỏ đô vì màu đó trong hệ
// thống mang nghĩa cảnh báo, ở đây không có gì để cảnh báo.
const MAU_THANH_PHAN: Record<string, string> = {
  du_dia_tai_viec: 'bg-navy-700',
  chat_luong_lich_su: 'bg-navy-500',
  tien_do_lich_su: 'bg-navy-300',
  khong_qua_han: 'bg-gold-500',
  kpi_gan_nhat: 'bg-gold-300',
};

/**
 * Điểm phù hợp tách theo 5 thành phần của công thức.
 *
 * Máy chủ vẫn trả `score_breakdown` và `weights` từ trước, nhưng giao diện chỉ in
 * đúng một con số tổng — nên người dùng thấy "82,3" mà không biết vì sao, và cái
 * lợi thế lớn nhất của công thức có trọng số (giải thích được từng thành phần) bị
 * bỏ không. Thanh dưới đây vẽ đúng phần điểm mỗi thành phần góp vào tổng.
 */
const ThanhThanhPhan = ({
  breakdown, weights,
}: {
  breakdown: Record<string, number>;
  weights: Record<string, number>;
}) => {
  const khoa = Object.keys(weights);
  if (khoa.length === 0) return null;

  return (
    <div className="mt-1.5">
      <div className="flex h-1.5 w-full bg-navy-100 rounded-sm overflow-hidden">
        {khoa.map(k => (
          <div
            key={k}
            className={MAU_THANH_PHAN[k] ?? 'bg-navy-400'}
            style={{ width: `${breakdown[k] ?? 0}%` }}
            title={`${NHAN_THANH_PHAN[k] ?? k}: ${(breakdown[k] ?? 0).toFixed(1)} / ${(weights[k] * 100).toFixed(0)} điểm`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-2.5 gap-y-0.5 mt-1">
        {khoa.map(k => (
          <span key={k} className="flex items-center gap-1 text-[10px] text-navy-500">
            <span className={`h-2 w-2 rounded-sm shrink-0 ${MAU_THANH_PHAN[k] ?? 'bg-navy-400'}`} />
            {NHAN_THANH_PHAN[k] ?? k}
            <span className="tabular text-navy-700">
              {(breakdown[k] ?? 0).toFixed(1)}/{(weights[k] * 100).toFixed(0)}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
};

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

  // Gợi ý phân công — mô hình chấm điểm phù hợp, chỉ tham khảo
  const [goiY, setGoiY] = useState<AssignmentResult | null>(null);
  const [dangGoiY, setDangGoiY] = useState(false);
  const [moBiLoai, setMoBiLoai] = useState(false);

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

  /*
    Gợi ý phụ thuộc độ mật, nhóm độ phức tạp và loại sản phẩm. Đổi một trong ba
    thì kết quả cũ không còn đúng nữa — xoá đi thay vì để người dùng chọn nhầm
    theo một bảng xếp hạng đã lỗi thời.
  */
  useEffect(() => {
    setGoiY(null);
    setMoBiLoai(false);
  }, [form.classification, form.complexity_group, form.product]);

  /*
    Danh sách chọn cán bộ = danh sách của trang Nhiệm vụ + những người được gợi ý.

    Cần gộp vì hai đầu mối không cùng phạm vi: `/employees/` mặc định chỉ trả
    vai staff và leader, còn mô hình gợi ý xét mọi vai trừ quản trị nên có thể
    đề xuất cả Trưởng phòng. Không gộp thì bấm chọn một người được gợi ý sẽ
    không hiện lên ô chọn — trạng thái đã gán đúng nhưng nhìn như chưa gán.
  */
  const dsCanBo = useMemo(() => {
    const m = new Map<string, { id: string; name: string }>();
    for (const u of users) m.set(u._id, { id: u._id, name: u.name });
    for (const s of goiY?.suggested ?? []) {
      if (!m.has(s.id)) m.set(s.id, { id: s.id, name: s.name });
    }
    return [...m.values()];
  }, [users, goiY]);

  const layGoiY = async () => {
    setDangGoiY(true);
    try {
      const kq = await aiApi.suggestAssignee({
        classification: form.classification,
        complexity_group: form.complexity_group,
        product: form.product,
        department_id: currentUser?.department_id,
        limit: 5,
      });
      setGoiY(kq);
      if (kq.suggested.length === 0) {
        toast('Không có cán bộ nào đủ điều kiện nhận nhiệm vụ này');
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Không lấy được gợi ý phân công');
    } finally {
      setDangGoiY(false);
    }
  };

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
                      {dsCanBo.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
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

                {/* Gợi ý phân công — mô hình chỉ xếp hạng, người có thẩm quyền quyết định */}
                {canEdit && !task?.is_redacted && (
                  <KhungMoHinh ma="goi_y_phan_cong">
                  <div className="mt-3 pt-3 border-t border-navy-100">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-[11px] text-navy-600 flex items-start gap-1.5">
                        <UserCheck size={13} className="shrink-0 mt-0.5 text-navy-500" />
                        <span>
                          Gợi ý cán bộ phù hợp — xét dư địa tải việc, chất lượng và tiến độ
                          lịch sử ở cùng nhóm nhiệm vụ, việc quá hạn và KPI các kỳ gần nhất.
                        </span>
                      </p>
                      <button
                        type="button" onClick={layGoiY} disabled={dangGoiY}
                        className="shrink-0 px-2.5 py-1 text-[11px] border border-navy-300 rounded-sm
                          text-navy-700 hover:bg-navy-50 disabled:opacity-50"
                      >
                        {dangGoiY ? 'Đang tính…' : goiY ? 'Tính lại' : 'Gợi ý cán bộ'}
                      </button>
                    </div>

                    {goiY && (
                      <div className="mt-2.5 space-y-1.5">
                        {goiY.suggested.map((s, i) => (
                          <button
                            key={s.id} type="button"
                            onClick={() => setForm(f => ({ ...f, assigned_to: s.id }))}
                            className={`w-full text-left border rounded-sm px-2.5 py-2 transition-colors
                              ${form.assigned_to === s.id
                                ? 'border-navy-600 bg-navy-50'
                                : 'border-navy-200 hover:bg-navy-50/60'}`}
                          >
                            <div className="flex items-baseline justify-between gap-2">
                              <p className="text-sm font-medium text-navy-800">
                                {i + 1}. {s.name}
                                {form.assigned_to === s.id && (
                                  <span className="ml-2 text-[10px] font-normal text-navy-500">đã chọn</span>
                                )}
                              </p>
                              <span className="text-sm font-bold text-navy-700 tabular shrink-0">
                                {s.score.toFixed(1)}
                              </span>
                            </div>
                            <p className="text-[11px] text-navy-500">{s.rank_position}</p>
                            <p className="text-[11px] text-navy-600 mt-0.5">
                              Tải việc {s.workload_percent}% ({s.open_points}/{s.capacity_points} điểm)
                              {s.tasks_overdue > 0 && ` · ${s.tasks_overdue} việc quá hạn`}
                              {s.recent_kpi != null && ` · KPI gần nhất ${s.recent_kpi}`}
                            </p>
                            <ThanhThanhPhan breakdown={s.score_breakdown} weights={goiY.weights} />
                            <ul className="mt-1 space-y-px">
                              {s.reasons.map((r, k) => (
                                <li key={k} className="text-[11px] text-navy-500">· {r}</li>
                              ))}
                            </ul>
                          </button>
                        ))}

                        {goiY.excluded.length > 0 && (
                          <div>
                            <button
                              type="button" onClick={() => setMoBiLoai(!moBiLoai)}
                              className="text-[11px] text-navy-500 hover:text-navy-700 flex items-center gap-1 py-1"
                            >
                              {moBiLoai ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                              {goiY.excluded.length} cán bộ bị loại khỏi danh sách
                            </button>
                            {moBiLoai && (
                              <ul className="space-y-1">
                                {goiY.excluded.map(e => (
                                  <li key={e.id} className="text-[11px] text-navy-600 bg-navy-50 rounded-sm px-2 py-1">
                                    <strong className="text-navy-800">{e.name}</strong>
                                    {e.rank_position && <span className="text-navy-400"> · {e.rank_position}</span>}
                                    <span className="block text-navy-500">{e.reason}</span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}

                        <p className="text-[10px] text-navy-400 leading-relaxed flex items-start gap-1 pt-1">
                          <Info size={11} className="shrink-0 mt-0.5" />
                          {goiY.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                  </KhungMoHinh>
                )}

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
