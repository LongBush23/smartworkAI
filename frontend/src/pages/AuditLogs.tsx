import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Shield, Search, Filter } from 'lucide-react';
import { format } from 'date-fns';

const AuditLogs = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [filterAction]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const url = filterAction ? `/audit/?action=${filterAction}` : '/audit/';
      const res = await api.get(url);
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const actionColors: any = {
    'auth.login': 'bg-blue-100 text-blue-800',
    'auth.logout': 'bg-gray-100 text-gray-800',
    'task.create': 'bg-green-100 text-green-800',
    'task.update': 'bg-yellow-100 text-yellow-800',
    'task.delete': 'bg-red-100 text-red-800',
    'task_request.auto_approved': 'bg-indigo-100 text-indigo-800',
    'task_request.approved': 'bg-emerald-100 text-emerald-800',
    'task_request.rejected': 'bg-rose-100 text-rose-800',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Shield className="text-gray-600" size={32} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Nhật ký Hệ thống (Audit Logs)</h1>
            <p className="text-sm text-gray-500">Lưu vết tất cả thao tác của người dùng để phục vụ thanh tra.</p>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Tìm kiếm log..." 
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg outline-none focus:border-blue-500 transition-colors text-sm"
            />
          </div>
          <div className="w-64 relative">
            <Filter className="absolute left-3 top-2.5 text-gray-400" size={18} />
            <select 
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg outline-none focus:border-blue-500 transition-colors text-sm appearance-none"
            >
              <option value="">Tất cả thao tác</option>
              <option value="auth.login">Đăng nhập</option>
              <option value="task.create">Tạo công việc</option>
              <option value="task.update">Cập nhật công việc</option>
              <option value="task.delete">Xóa công việc</option>
              <option value="task_request.auto_approved">AI tự động duyệt</option>
              <option value="task_request.approved">Quản lý duyệt</option>
              <option value="task_request.rejected">Quản lý từ chối</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-10 text-gray-500">Đang tải nhật ký...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thời gian</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Người dùng</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hành động</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tài nguyên</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chi tiết / IP</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log: any) => (
                  <tr key={log._id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(log.created_at), 'dd/MM/yyyy HH:mm:ss')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{log.user_name || 'Hệ thống'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${actionColors[log.action] || 'bg-gray-100 text-gray-800'}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.resource_type} <br/>
                      <span className="text-xs text-gray-400">{log.resource_id}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div className="truncate max-w-xs" title={log.details}>{log.details || '-'}</div>
                      <div className="text-xs text-gray-400 mt-1">{log.ip_address}</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {logs.length === 0 && (
              <div className="text-center py-10 text-gray-500">Không tìm thấy nhật ký.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogs;
