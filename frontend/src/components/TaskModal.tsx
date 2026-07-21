import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { X, Send, Paperclip, CheckSquare, Clock } from 'lucide-react';

interface SubTask {
  id: string;
  title: string;
  is_completed: boolean;
}

interface Comment {
  _id: string;
  content: string;
  user_name: string;
  created_at: string;
}

export const TaskModal = ({ task, projects, users, isOpen, onClose, onSave, onDelete }: any) => {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState('details'); // details, subtasks, comments
  const [formData, setFormData] = useState({
    title: task?.title || '',
    description: task?.description || '',
    project_id: task?.project_id || (projects.length > 0 ? projects[0]._id : ''),
    assigned_to: task?.assigned_to || '',
    status: task?.status || 'todo',
    deadline: task?.deadline ? task.deadline.split('T')[0] : new Date().toISOString().split('T')[0],
    effort_required: task?.effort_required || 1,
    subtasks: task?.subtasks || [],
  });

  // Comments state
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');

  // Subtasks state
  const [newSubtask, setNewSubtask] = useState('');
  
  // AI Recommendation state
  const [aiCandidates, setAiCandidates] = useState<any[]>([]);
  const [isAiLoading, setIsAiLoading] = useState(false);

  useEffect(() => {
    if (task && activeTab === 'comments') {
      fetchComments();
    }
    // Clear candidates when modal closes/opens
    if (!isOpen) {
      setAiCandidates([]);
    }
  }, [task, activeTab, isOpen]);

  const fetchComments = async () => {
    try {
      const res = await api.get(`/tasks/${task._id}/comments`);
      setComments(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handlePostComment = async () => {
    if (!newComment.trim()) return;
    try {
      const res = await api.post(`/tasks/${task._id}/comments`, { content: newComment });
      setComments([...comments, res.data]);
      setNewComment('');
    } catch (err) {
      toast.error('Lỗi đăng bình luận');
    }
  };

  const handleAddSubtask = () => {
    if (!newSubtask.trim()) return;
    const st = { id: Math.random().toString(36).substr(2, 9), title: newSubtask, is_completed: false };
    setFormData({ ...formData, subtasks: [...formData.subtasks, st] });
    setNewSubtask('');
  };

  const toggleSubtask = (id: string) => {
    const updated = formData.subtasks.map((st: any) => 
      st.id === id ? { ...st, is_completed: !st.is_completed } : st
    );
    setFormData({ ...formData, subtasks: updated });
  };

  const removeSubtask = (id: string) => {
    setFormData({ ...formData, subtasks: formData.subtasks.filter((st: any) => st.id !== id) });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ ...formData, assigned_to: formData.assigned_to || null });
  };

  const handleSuggestAI = async () => {
    if (!task?._id) return;
    try {
      setIsAiLoading(true);
      const res = await api.get(`/ai/optimize-resources/${task._id}`);
      setAiCandidates(res.data.top_candidates || []);
      if (res.data.top_candidates?.length === 0) {
        toast.error('Không tìm thấy nhân viên phù hợp');
      }
    } catch (err) {
      toast.error('Lỗi khi tải gợi ý AI');
    } finally {
      setIsAiLoading(false);
    }
  };

  const subtasksCompleted = formData.subtasks.filter((st: any) => st.is_completed).length;
  const subtasksTotal = formData.subtasks.length;
  const progressPercent = subtasksTotal > 0 ? Math.round((subtasksCompleted / subtasksTotal) * 100) : 0;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 shrink-0">
          <h2 className="text-xl font-bold text-gray-800">{task ? 'Chi tiết Công việc' : 'Tạo Công việc mới'}</h2>
          <button onClick={onClose} className="p-2 text-gray-500 hover:bg-gray-100 rounded-full transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        {task && (
          <div className="flex border-b border-gray-200 px-6 shrink-0 bg-gray-50">
            <button onClick={() => setActiveTab('details')} className={`px-4 py-3 text-sm font-medium border-b-2 ${activeTab === 'details' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Thông tin chung</button>
            <button onClick={() => setActiveTab('subtasks')} className={`px-4 py-3 text-sm font-medium border-b-2 flex items-center gap-2 ${activeTab === 'subtasks' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              <CheckSquare size={16} /> Sub-tasks ({subtasksCompleted}/{subtasksTotal})
            </button>
            <button onClick={() => setActiveTab('comments')} className={`px-4 py-3 text-sm font-medium border-b-2 flex items-center gap-2 ${activeTab === 'comments' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              Bình luận
            </button>
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-white">
          
          {/* TAB: DETAILS */}
          {activeTab === 'details' && (
            <form id="task-form" onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tên công việc</label>
                <input required type="text" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow outline-none" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mô tả chi tiết</label>
                <textarea required rows={3} value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow outline-none"></textarea>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Thuộc dự án</label>
                  <select required value={formData.project_id} onChange={e => setFormData({...formData, project_id: e.target.value})} className="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none">
                    <option value="">Chọn dự án</option>
                    {projects.map((p: any) => <option key={p._id} value={p._id}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-sm font-medium text-gray-700">Người thực hiện</label>
                    {task && (
                      <button 
                        type="button"
                        onClick={handleSuggestAI} 
                        disabled={isAiLoading}
                        className="text-xs flex items-center gap-1 text-indigo-600 hover:text-indigo-800 font-medium bg-indigo-50 px-2 py-0.5 rounded"
                      >
                        {isAiLoading ? 'Đang phân tích...' : '✨ Gợi ý AI'}
                      </button>
                    )}
                  </div>
                  <select value={formData.assigned_to} onChange={e => setFormData({...formData, assigned_to: e.target.value})} className="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Chưa phân công</option>
                    {users.map((u: any) => <option key={u._id} value={u._id}>{u.name}</option>)}
                  </select>

                  {aiCandidates.length > 0 && (
                    <div className="mt-2 bg-indigo-50/50 border border-indigo-100 rounded-lg p-3 space-y-2">
                      <p className="text-xs font-semibold text-indigo-800 uppercase tracking-wider mb-2">Top nhân sự phù hợp (Theo NLP)</p>
                      {aiCandidates.map(c => (
                        <div key={c._id} className="flex justify-between items-center bg-white p-2 rounded border border-indigo-50 shadow-sm">
                          <div>
                            <p className="text-sm font-medium text-gray-800">{c.name}</p>
                            <p className="text-[10px] text-gray-500 line-clamp-1">Kỹ năng: {c.skills?.join(', ') || 'Chưa cập nhật'}</p>
                          </div>
                          <div className="flex flex-col items-end">
                            <span className="text-xs font-bold text-emerald-600">{c.nlp_similarity.toFixed(0)}% Khớp</span>
                            <button 
                              type="button"
                              onClick={() => {
                                setFormData({...formData, assigned_to: c._id});
                                setAiCandidates([]);
                              }}
                              className="text-[10px] bg-indigo-600 text-white px-2 py-1 rounded mt-1 hover:bg-indigo-700"
                            >
                              Chọn
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Hạn chót (Deadline)</label>
                  <input required type="date" value={formData.deadline} onChange={e => setFormData({...formData, deadline: e.target.value})} className="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Trạng thái</label>
                  <select value={formData.status} onChange={e => setFormData({...formData, status: e.target.value})} className="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none">
                    <option value="todo">Cần làm</option>
                    <option value="in_progress">Đang làm</option>
                    <option value="review">Chờ duyệt</option>
                    <option value="done">Hoàn thành</option>
                  </select>
                </div>
              </div>
            </form>
          )}

          {/* TAB: SUBTASKS */}
          {activeTab === 'subtasks' && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-gray-200 rounded-full h-2.5">
                  <div className="bg-blue-600 h-2.5 rounded-full transition-all" style={{ width: `${progressPercent}%` }}></div>
                </div>
                <span className="text-sm font-medium text-gray-600">{progressPercent}%</span>
              </div>
              
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={newSubtask} 
                  onChange={e => setNewSubtask(e.target.value)} 
                  onKeyPress={e => e.key === 'Enter' && handleAddSubtask()}
                  placeholder="Nhập tên việc nhỏ cần làm..." 
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg outline-none text-sm"
                />
                <button onClick={handleAddSubtask} className="bg-gray-100 text-gray-700 hover:bg-gray-200 px-4 py-2 rounded-lg text-sm font-semibold">Thêm</button>
              </div>

              <div className="space-y-2 mt-4">
                {formData.subtasks.map((st: any) => (
                  <div key={st.id} className="flex items-center justify-between p-3 border border-gray-100 rounded-lg bg-gray-50 hover:bg-white transition-colors">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" checked={st.is_completed} onChange={() => toggleSubtask(st.id)} className="w-5 h-5 text-blue-600 rounded" />
                      <span className={`text-sm ${st.is_completed ? 'line-through text-gray-400' : 'text-gray-700 font-medium'}`}>{st.title}</span>
                    </label>
                    <button onClick={() => removeSubtask(st.id)} className="text-gray-400 hover:text-red-500">
                      <X size={16} />
                    </button>
                  </div>
                ))}
                {formData.subtasks.length === 0 && (
                  <div className="text-center py-8 text-gray-400 text-sm">Chưa có sub-tasks nào.</div>
                )}
              </div>
            </div>
          )}

          {/* TAB: COMMENTS */}
          {activeTab === 'comments' && (
            <div className="flex flex-col h-[400px]">
              <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
                {comments.length === 0 ? (
                  <div className="text-center py-10 text-gray-400 text-sm">Chưa có bình luận nào. Bắt đầu thảo luận nhé!</div>
                ) : (
                  comments.map(c => (
                    <div key={c._id} className="flex flex-col">
                      <div className="flex items-baseline gap-2 mb-1">
                        <span className="font-semibold text-gray-800 text-sm">{c.user_name}</span>
                        <span className="text-xs text-gray-400">{format(new Date(c.created_at), 'dd/MM HH:mm')}</span>
                      </div>
                      <div className="bg-gray-100 px-4 py-2.5 rounded-2xl rounded-tl-sm w-fit max-w-[85%] text-sm text-gray-800">
                        {c.content}
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="shrink-0 flex items-center gap-2 border-t pt-4">
                <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors">
                  <Paperclip size={20} />
                </button>
                <input 
                  type="text" 
                  value={newComment}
                  onChange={e => setNewComment(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && handlePostComment()}
                  placeholder="Viết bình luận..." 
                  className="flex-1 bg-gray-100 border-transparent focus:bg-white focus:border-blue-500 focus:ring-0 rounded-full px-4 py-2 text-sm outline-none transition-colors border"
                />
                <button onClick={handlePostComment} className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors">
                  <Send size={18} className="ml-0.5" />
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Footer (only visible in Details/Subtasks tab to allow saving) */}
        {activeTab !== 'comments' && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between shrink-0 rounded-b-xl">
            {task && (
              <button type="button" onClick={() => onDelete(task._id)} className="text-red-600 hover:text-red-800 text-sm font-semibold px-3 py-2">
                Xóa công việc
              </button>
            )}
            {!task && <div></div>}
            <div className="flex gap-3">
              <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg text-sm font-semibold shadow-sm">
                Hủy
              </button>
              <button type="submit" form="task-form" className="px-5 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold shadow-sm shadow-blue-200">
                Lưu thay đổi
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
