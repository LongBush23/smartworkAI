import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Plus, Edit2, Trash2, Mail, Briefcase } from 'lucide-react';
import toast from 'react-hot-toast';

interface User {
  _id: string;
  name: string;
  username: string;
  email: string;
  role: string;
  department_id: string | null;
  skills: string[];
  availability: number;
}

const Employees = () => {
  const [employees, setEmployees] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<User | null>(null);

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: '',
    email: '',
    department_id: '',
    skills: '' // comma separated string for form
  });

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const res = await api.get('/employees/');
      setEmployees(res.data);
    } catch (err) {
      console.error(err);
      toast.error('Lỗi tải danh sách nhân sự');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleOpenModal = (emp?: User) => {
    if (emp) {
      setEditingEmployee(emp);
      setFormData({
        username: emp.username,
        password: '', // blank when editing
        name: emp.name,
        email: emp.email,
        department_id: emp.department_id || '',
        skills: emp.skills ? emp.skills.map((s: any) => s.skill_name || s).join(', ') : ''
      });
    } else {
      setEditingEmployee(null);
      setFormData({
        username: '',
        password: '',
        name: '',
        email: '',
        department_id: '',
        skills: ''
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    try {
      const payload: any = {
        username: formData.username,
        name: formData.name,
        email: formData.email,
        department_id: formData.department_id === '' ? null : formData.department_id,
        skills: formData.skills.split(',').map(s => s.trim()).filter(s => s !== '').map(s => ({ skill_name: s, self_rating: 3 }))
      };
      
      if (!editingEmployee) {
        payload.password = formData.password;
      }

      if (editingEmployee) {
        await api.put(`/employees/${editingEmployee._id}`, payload);
        toast.success('Đã cập nhật nhân sự');
      } else {
        await api.post('/employees/', payload);
        toast.success('Đã thêm nhân sự');
      }
      setIsModalOpen(false);
      fetchEmployees();
    } catch (err) {
      console.error(err);
      toast.error('Lỗi cập nhật nhân sự');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Bạn có chắc muốn xóa nhân sự này?')) {
      try {
        await api.delete(`/employees/${id}`);
        toast.success('Đã xóa nhân sự');
        fetchEmployees();
      } catch (err) {
        console.error(err);
        toast.error('Lỗi khi xóa nhân sự');
      }
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Quản lý Nhân sự</h1>
        <button 
          onClick={() => handleOpenModal()}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-medium"
        >
          <Plus size={20} />
          <span>Thêm Nhân sự</span>
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="p-4 font-semibold text-gray-600">Nhân sự</th>
              <th className="p-4 font-semibold text-gray-600">Kỹ năng</th>
              <th className="p-4 font-semibold text-gray-600">Khả dụng</th>
              <th className="p-4 font-semibold text-gray-600 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="p-4 text-center">Đang tải...</td></tr>
            ) : employees.length === 0 ? (
              <tr><td colSpan={4} className="p-4 text-center">Chưa có dữ liệu</td></tr>
            ) : (
              employees.map((emp) => (
                <tr key={emp._id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-lg">
                        {emp.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">{emp.name}</p>
                        <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                          <Mail size={12} />
                          <span>{emp.email}</span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-gray-500 mt-0.5">
                          <Briefcase size={12} />
                          <span>Mã phòng ban: {emp.department_id || 'Trống'}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-1">
                      {emp.skills && emp.skills.map((skill: any, i: number) => (
                        <span key={i} className="px-2 py-1 bg-indigo-50 text-indigo-600 text-xs rounded-md border border-indigo-100">
                          {skill.skill_name || skill}
                        </span>
                      ))}
                      {(!emp.skills || emp.skills.length === 0) && <span className="text-gray-400 text-xs">Chưa có dữ liệu</span>}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div className={`h-2 rounded-full ${emp.availability < 50 ? 'bg-red-500' : 'bg-emerald-500'}`} style={{ width: `${emp.availability}%` }}></div>
                      </div>
                      <span className="text-sm font-medium text-gray-700">{emp.availability}%</span>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <button onClick={() => handleOpenModal(emp)} className="text-gray-400 hover:text-blue-600 p-2">
                      <Edit2 size={18} />
                    </button>
                    <button onClick={() => handleDelete(emp._id)} className="text-gray-400 hover:text-red-600 p-2 ml-1">
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-xl font-bold mb-4">{editingEmployee ? 'Sửa Nhân sự' : 'Thêm Nhân sự mới'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tên đăng nhập</label>
                  <input required type="text" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Mật khẩu {editingEmployee && '(Bỏ trống nếu không đổi)'}</label>
                  <input type="password" required={!editingEmployee} value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Họ tên</label>
                  <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <input required type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Mã Phòng ban (Tùy chọn)</label>
                <input type="text" value={formData.department_id} onChange={e => setFormData({...formData, department_id: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Kỹ năng (cách nhau bởi dấu phẩy)</label>
                <input type="text" placeholder="Python, React, Quản lý..." value={formData.skills} onChange={e => setFormData({...formData, skills: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md font-medium">Hủy</button>
                <button type="submit" disabled={saving} className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed">
                  {saving ? 'Đang lưu...' : 'Lưu'}
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
