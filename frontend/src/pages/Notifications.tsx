import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import toast from 'react-hot-toast';
import { Bell, Check, CheckCheck, Clock, Info, AlertTriangle } from 'lucide-react';

const TYPE_STYLES: Record<string, { icon: React.ReactNode; color: string }> = {
  task_assigned: { icon: <Check size={16} />, color: 'text-blue-600 bg-blue-100' },
  request_approved: { icon: <Check size={16} />, color: 'text-emerald-600 bg-emerald-100' },
  request_auto_approved: { icon: <Check size={16} />, color: 'text-emerald-600 bg-emerald-100' },
  request_rejected: { icon: <AlertTriangle size={16} />, color: 'text-red-600 bg-red-100' },
  request_submitted: { icon: <Info size={16} />, color: 'text-amber-600 bg-amber-100' },
  deadline_warning: { icon: <Clock size={16} />, color: 'text-orange-600 bg-orange-100' },
  task_overdue: { icon: <AlertTriangle size={16} />, color: 'text-red-600 bg-red-100' },
  general: { icon: <Bell size={16} />, color: 'text-gray-600 bg-gray-100' },
};

const Notifications = () => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications/');
      setNotifications(res.data);
    } catch {
      toast.error('Không thể tải thông báo');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: string) => {
    await api.put(`/notifications/${id}/read`);
    setNotifications(notifications.map(n => n._id === id ? { ...n, is_read: true } : n));
    window.dispatchEvent(new Event('notificationRead'));
  };

  const markAllAsRead = async () => {
    await api.put('/notifications/read-all');
    setNotifications(notifications.map(n => ({ ...n, is_read: true })));
    toast.success('Đã đánh dấu tất cả đã đọc');
    window.dispatchEvent(new Event('notificationRead'));
  };

  const timeAgo = (dateStr: string) => {
    const now = new Date();
    const date = new Date(dateStr);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} giờ trước`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} ngày trước`;
  };

  if (loading) return <div className="flex items-center justify-center h-64">Đang tải...</div>;

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Bell className="text-blue-600" /> Thông báo
          {unreadCount > 0 && (
            <span className="bg-red-500 text-white text-sm font-bold px-2 py-0.5 rounded-full">{unreadCount}</span>
          )}
        </h1>
        {unreadCount > 0 && (
          <button onClick={markAllAsRead} className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
            <CheckCheck size={16} /> Đánh dấu tất cả đã đọc
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Bell size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Chưa có thông báo nào</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((notif) => {
            const style = TYPE_STYLES[notif.type] || TYPE_STYLES.general;
            return (
              <div
                key={notif._id}
                onClick={() => !notif.is_read && markAsRead(notif._id)}
                className={`bg-white rounded-xl border p-4 flex items-start gap-4 cursor-pointer transition-all hover:shadow-sm ${
                  notif.is_read ? 'border-gray-100 opacity-70' : 'border-blue-200 bg-blue-50/30'
                }`}
              >
                <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${style.color}`}>
                  {style.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${notif.is_read ? 'text-gray-700' : 'text-gray-900 font-semibold'}`}>
                    {notif.title}
                  </p>
                  <p className="text-sm text-gray-500 mt-0.5">{notif.message}</p>
                  <p className="text-xs text-gray-400 mt-1">{timeAgo(notif.created_at)}</p>
                </div>
                {!notif.is_read && (
                  <div className="w-2.5 h-2.5 bg-blue-500 rounded-full shrink-0 mt-1.5"></div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Notifications;
