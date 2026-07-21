import { useState, useEffect } from 'react';
import api from '../lib/api';
import toast from 'react-hot-toast';
import { ClipboardCheck, Check, X, Clock, TrendingUp, User } from 'lucide-react';

const TaskRequests = () => {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('pending');
  const [rejectReason, setRejectReason] = useState('');
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  useEffect(() => {
    fetchRequests();
  }, [filterStatus]);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/tasks/requests?status=${filterStatus}`);
      setRequests(res.data);
    } catch {
      toast.error('Không thể tải danh sách yêu cầu');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await api.put(`/tasks/requests/${id}/approve`);
      toast.success('Đã duyệt yêu cầu thành công');
      fetchRequests();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Lỗi duyệt yêu cầu');
    }
  };

  const handleReject = async (id: string) => {
    try {
      await api.put(`/tasks/requests/${id}/reject`, { reject_reason: rejectReason });
      toast.success('Đã từ chối yêu cầu');
      setRejectingId(null);
      setRejectReason('');
      fetchRequests();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Lỗi từ chối yêu cầu');
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-700 bg-emerald-100';
    if (score >= 60) return 'text-amber-700 bg-amber-100';
    return 'text-red-700 bg-red-100';
  };

  const getStatusBadge = (status: string) => {
    const map: Record<string, { label: string; cls: string }> = {
      pending: { label: 'Chờ duyệt', cls: 'bg-amber-100 text-amber-700' },
      approved: { label: 'Đã duyệt', cls: 'bg-emerald-100 text-emerald-700' },
      auto_approved: { label: 'AI Tự duyệt', cls: 'bg-blue-100 text-blue-700' },
      rejected: { label: 'Từ chối', cls: 'bg-red-100 text-red-700' },
    };
    const s = map[status] || { label: status, cls: 'bg-gray-100 text-gray-700' };
    return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${s.cls}`}>{s.label}</span>;
  };

  const timeAgo = (dateStr: string) => {
    const diffMs = Date.now() - new Date(dateStr).getTime();
    const diffHours = Math.floor(diffMs / 3600000);
    if (diffHours < 1) return 'Vừa gửi';
    if (diffHours < 24) return `${diffHours}h trước`;
    return `${Math.floor(diffHours / 24)} ngày trước`;
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <ClipboardCheck className="text-blue-600" /> Quản lý Yêu cầu Tham gia
      </h1>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { key: 'pending', label: 'Chờ duyệt' },
          { key: 'approved', label: 'Đã duyệt' },
          { key: 'auto_approved', label: 'AI Tự duyệt' },
          { key: 'rejected', label: 'Từ chối' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilterStatus(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterStatus === tab.key ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">Đang tải...</div>
      ) : requests.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <ClipboardCheck size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Không có yêu cầu nào trong mục "{filterStatus}"</p>
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((req) => (
            <div key={req._id} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
                      <User size={20} />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">{req.employee_name || 'Nhân viên'}</p>
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock size={12} /> {timeAgo(req.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="ml-13 space-y-2">
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">Công việc:</span> {req.task_title || req.task_id}
                    </p>
                    {req.message && (
                      <p className="text-sm text-gray-600 italic bg-gray-50 p-2 rounded-lg">"{req.message}"</p>
                    )}
                    {req.reject_reason && (
                      <p className="text-sm text-red-600 bg-red-50 p-2 rounded-lg">Lý do từ chối: {req.reject_reason}</p>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2 ml-4">
                  {getStatusBadge(req.status)}
                  <div className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${getScoreColor(req.ai_match_score || 0)}`}>
                    <TrendingUp size={14} />
                    {req.ai_match_score ?? 0}% Match
                  </div>
                </div>
              </div>

              {/* Action Buttons (only for pending) */}
              {req.status === 'pending' && (
                <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-3">
                  <button
                    onClick={() => handleApprove(req._id)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors"
                  >
                    <Check size={16} /> Duyệt
                  </button>
                  
                  {rejectingId === req._id ? (
                    <div className="flex items-center gap-2 flex-1">
                      <input
                        type="text"
                        placeholder="Lý do từ chối..."
                        value={rejectReason}
                        onChange={e => setRejectReason(e.target.value)}
                        className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-red-500"
                        autoFocus
                      />
                      <button onClick={() => handleReject(req._id)} className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-sm font-medium">
                        Xác nhận
                      </button>
                      <button onClick={() => { setRejectingId(null); setRejectReason(''); }} className="text-gray-500 hover:text-gray-700 px-2">
                        Huỷ
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setRejectingId(req._id)}
                      className="bg-white border border-red-300 text-red-600 hover:bg-red-50 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors"
                    >
                      <X size={16} /> Từ chối
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TaskRequests;
