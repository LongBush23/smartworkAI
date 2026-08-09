import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Plus, Edit2, Trash2, Mail, Users, X, Building2 } from 'lucide-react';
import api from '../lib/api';
import { layMe } from '../lib/me';

interface Employee {
  _id: string;
  username: string;
  name: string;
  email: string;
  role: 'admin' | 'director' | 'leader' | 'staff';
  department_id?: string;
  position?: string;
  rank?: string;
  is_commander?: boolean;
}

interface Department {
  _id: string;
  name: string;
  force_system?: string;
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Quản trị hệ thống',
  director: 'Lãnh đạo đơn vị',
  leader: 'Lãnh đạo, chỉ huy',
  staff: 'Cán bộ, chiến sĩ',
};

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-700',
  director: 'bg-red-100 text-red-700',
  leader: 'bg-amber-100 text-amber-700',
  staff: 'bg-blue-100 text-blue-700',
};

const RANKS = [
  'Thượng sĩ', 'Thiếu úy', 'Trung úy', 'Thượng úy', 'Đại úy',
  'Thiếu tá', 'Trung tá', 'Thượng tá', 'Đại tá',
];

const emptyForm = {
  username: '', name: '', email: '', password: '',
  role: 'staff' as Employee['role'],
  department_id: '', position: '', rank: '',
};

const Employees = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [deptFilter, setDeptFilter] = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [meRes, empRes, deptRes] = await Promise.all([
        layMe().then(data => ({ data })),
        api.get('/employees/', { params: { role: '' } }).catch(() => ({ data: [] })),
        api.get('/departments/').catch(() => ({ data: [] })),
      ]);
      setMe(meRes.data);
      setEmployees(empRes.data);
      setDepartments(deptRes.data);
    } catch (error) {
      console.error('Không tải được danh sách cán bộ', error);
    } finally {
      setLoading(false);
    }
  };

  const deptName = (id?: string) => departments.find(d => d._id === id)?.name ?? '—';

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyForm, department_id: me?.department_id ?? '' });
    setShowModal(true);
  };

  const openEdit = (emp: Employee) => {
    setEditing(emp);
    setForm({
      username: emp.username, name: emp.name, email: emp.email, password: '',
      role: emp.role, department_id: emp.department_id ?? '',
      position: emp.position ?? '', rank: emp.rank ?? '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        name: form.name, email: form.email, role: form.role,
        department_id: form.department_id || undefined,
        position: form.position || undefined,
        rank: form.rank || undefined,
      };
      if (editing) {
        await api.put(`/employees/${editing._id}`, payload);
        toast.success('Đã cập nhật cán bộ');
      } else {
        await api.post('/employees/', { ...payload, username: form.username, password: form.password });
        toast.success('Đã thêm cán bộ');
      }
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Không lưu được thông tin cán bộ');
    }
  };

  const handleDelete = async (emp: Employee) => {
    if (!confirm(`Xoá cán bộ "${emp.name}"?`)) return;
    try {
      await api.delete(`/employees/${emp._id}`);
      toast.success('Đã xoá cán bộ');
      fetchData();
    } catch { toast.error('Không xoá được cán bộ'); }
  };

  const filtered = deptFilter ? employees.filter(e => e.department_id === deptFilter) : employees;

  // Thống kê theo nhóm để đối chiếu điểm D (tỷ lệ cán bộ thuộc quyền quản lý)
  const commanderCount = filtered.filter(e => e.role === 'director' || e.role === 'leader').length;

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3 justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Users className="h-6 w-6 text-blue-600" /> Cán bộ / Đơn vị
        </h1>
        <div className="flex items-center gap-2">
          <select
            value={deptFilter}
            onChange={e => setDeptFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            <option value="">Tất cả đơn vị</option>
            {departments.map(d => <option key={d._id} value={d._id}>{d.name}</option>)}
          </select>
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            <Plus size={18} /> Thêm cán bộ
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500">Tổng số cán bộ</p>
          <p className="text-2xl font-bold text-gray-800 mt-1">{filtered.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500">Lãnh đạo, chỉ huy</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{commanderCount}</p>
          <p className="text-[11px] text-gray-400 mt-0.5">KPI tính theo 04 tiêu chí</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-xs text-gray-500 flex items-center gap-1"><Building2 size={12} /> Số đơn vị</p>
          <p className="text-2xl font-bold text-indigo-600 mt-1">{departments.length}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {filtered.length === 0 ? (
          <p className="p-12 text-center text-gray-500">Chưa có cán bộ nào.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-600">
                  <th className="p-3 font-medium">Họ và tên</th>
                  <th className="p-3 font-medium">Cấp bậc</th>
                  <th className="p-3 font-medium">Chức vụ</th>
                  <th className="p-3 font-medium">Đơn vị</th>
                  <th className="p-3 font-medium">Thẩm quyền</th>
                  <th className="p-3 font-medium text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(emp => (
                  <tr key={emp._id} className="hover:bg-gray-50">
                    <td className="p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
                          {emp.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-800">{emp.name}</p>
                          <p className="text-xs text-gray-500 flex items-center gap-1 truncate">
                            <Mail size={11} /> {emp.email}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="p-3 text-gray-600">{emp.rank || '—'}</td>
                    <td className="p-3 text-gray-600">{emp.position || '—'}</td>
                    <td className="p-3 text-gray-600">{deptName(emp.department_id)}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${ROLE_COLORS[emp.role]}`}>
                        {ROLE_LABELS[emp.role]}
                      </span>
                    </td>
                    <td className="p-3">
                      <div className="flex items-center justify-center gap-1">
                        <button onClick={() => openEdit(emp)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded">
                          <Edit2 size={15} />
                        </button>
                        <button onClick={() => handleDelete(emp)} className="p-1.5 text-red-500 hover:bg-red-50 rounded">
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 h-14 border-b border-gray-200">
              <h2 className="font-semibold text-gray-800">{editing ? 'Sửa thông tin cán bộ' : 'Thêm cán bộ'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><X size={22} /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {!editing && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tên đăng nhập *</label>
                    <input
                      required value={form.username}
                      onChange={e => setForm({ ...form, username: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu *</label>
                    <input
                      required type="password" value={form.password}
                      onChange={e => setForm({ ...form, password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                </div>
              )}

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

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cấp bậc hàm</label>
                  <select
                    value={form.rank}
                    onChange={e => setForm({ ...form, rank: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">— Chưa xác định —</option>
                    {RANKS.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Chức vụ</label>
                  <input
                    value={form.position}
                    placeholder="VD: Trưởng phòng, Chuyên viên"
                    onChange={e => setForm({ ...form, position: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Đơn vị</label>
                  <select
                    value={form.department_id}
                    onChange={e => setForm({ ...form, department_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">— Chưa phân công —</option>
                    {departments.map(d => <option key={d._id} value={d._id}>{d.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Thẩm quyền</label>
                  <select
                    value={form.role}
                    onChange={e => setForm({ ...form, role: e.target.value as Employee['role'] })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="staff">Cán bộ, chiến sĩ</option>
                    <option value="leader">Lãnh đạo, chỉ huy</option>
                    {me?.role === 'admin' && <option value="director">Lãnh đạo đơn vị</option>}
                    {me?.role === 'admin' && <option value="admin">Quản trị hệ thống</option>}
                  </select>
                  {(form.role === 'leader' || form.role === 'director') && (
                    <p className="text-[11px] text-amber-700 mt-1">
                      KPI sẽ tính theo 04 tiêu chí (có điểm D về kết quả lãnh đạo, chỉ đạo).
                    </p>
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50">
                  Huỷ
                </button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                  {editing ? 'Lưu thay đổi' : 'Thêm cán bộ'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Employees;
