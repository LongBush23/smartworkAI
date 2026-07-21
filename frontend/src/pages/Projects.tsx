import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Plus, Edit2, Trash2, Brain, Activity, Clock, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

interface Project {
  _id: string;
  name: string;
  description: string;
  status: string;
  start_date: string;
  end_date: string;
  progress: number;
}

const Projects = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  
  // Details Modal state
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectMembers, setProjectMembers] = useState<any[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const navigate = useNavigate();
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'planning',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0],
  });

  // AI State
  const [aiPrediction, setAiPrediction] = useState<any>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [predictError, setPredictError] = useState('');

  const handlePredictAI = async (project: Project, embedded = false) => {
    if (!embedded) setIsAiModalOpen(true);
    setIsPredicting(true);
    setPredictError('');
    setAiPrediction(null);
    try {
      const res = await api.get(`/ai/predict-deadline/${project._id}`);
      setAiPrediction(res.data);
    } catch (err) {
      console.error(err);
      setPredictError('Lỗi kết nối hoặc dự án chưa đủ dữ liệu để AI phân tích.');
    } finally {
      setIsPredicting(false);
    }
  };

  const openDetailsModal = async (proj: Project) => {
    setSelectedProject(proj);
    setDetailsModalOpen(true);
    setAiPrediction(null);
    setPredictError('');
    
    try {
      setLoadingMembers(true);
      const res = await api.get(`/tasks/?project_id=${proj._id}`);
      const projectTasks = res.data;
      
      const membersMap = new Map();
      projectTasks.forEach((t: any) => {
        if (t.assigned_to && t.assignee_name) {
          if (!membersMap.has(t.assigned_to)) {
            membersMap.set(t.assigned_to, {
              id: t.assigned_to,
              name: t.assignee_name,
              taskCount: 1
            });
          } else {
            membersMap.get(t.assigned_to).taskCount += 1;
          }
        }
      });
      setProjectMembers(Array.from(membersMap.values()));
    } catch (err) {
      console.error('Error fetching project members:', err);
    } finally {
      setLoadingMembers(false);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const res = await api.get('/projects/');
      setProjects(res.data);
    } catch (err) {
      console.error(err);
      toast.error('Lỗi tải danh sách dự án');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleOpenModal = (project?: Project) => {
    if (project) {
      setEditingProject(project);
      setFormData({
        name: project.name,
        description: project.description,
        status: project.status,
        start_date: project.start_date.split('T')[0],
        end_date: project.end_date.split('T')[0],
      });
    } else {
      setEditingProject(null);
      setFormData({
        name: '',
        description: '',
        status: 'planning',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0],
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingProject) {
        await api.put(`/projects/${editingProject._id}`, formData);
        toast.success('Đã cập nhật dự án');
      } else {
        await api.post('/projects/', formData);
        toast.success('Đã tạo dự án mới');
      }
      setIsModalOpen(false);
      fetchProjects();
    } catch (err) {
      console.error(err);
      toast.error('Có lỗi xảy ra khi lưu dự án');
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Bạn có chắc muốn xóa dự án này?')) {
      try {
        await api.delete(`/projects/${id}`);
        toast.success('Đã xóa dự án');
        fetchProjects();
      } catch (err) {
        console.error(err);
        toast.error('Lỗi khi xóa dự án');
      }
    }
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className="text-2xl font-bold text-gray-800">Quản lý Dự án</h1>
        <button 
          onClick={() => handleOpenModal()}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-medium"
        >
          <Plus size={20} />
          <span>Thêm Dự án</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-10 text-gray-500 bg-white rounded-xl shadow-sm border border-gray-200">Đang tải...</div>
        ) : projects.length === 0 ? (
          <div className="col-span-full text-center py-10 text-gray-500 bg-white rounded-xl shadow-sm border border-gray-200">Chưa có dự án nào</div>
        ) : (
          projects.map((proj) => (
            <div key={proj._id} onClick={() => openDetailsModal(proj)} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-all duration-200 flex flex-col group cursor-pointer">
              <div className="p-5 flex-1">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-bold text-gray-800 line-clamp-2 pr-2 group-hover:text-blue-600 transition-colors">{proj.name}</h3>
                  <span className={`shrink-0 px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider
                    ${proj.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 
                      proj.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 
                      proj.status === 'delayed' ? 'bg-red-100 text-red-700' : 
                      'bg-gray-100 text-gray-700'}`}>
                    {proj.status === 'completed' ? 'Hoàn thành' : 
                     proj.status === 'in_progress' ? 'Đang chạy' : 
                     proj.status === 'delayed' ? 'Trễ hạn' : 'Kế hoạch'}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mb-6 line-clamp-3 leading-relaxed">{proj.description}</p>
                
                <div className="mb-2">
                  <div className="flex justify-between text-xs mb-1.5 font-semibold">
                    <span className="text-gray-500 uppercase tracking-wider">Tiến độ</span>
                    <span className={proj.progress === 100 ? 'text-emerald-600' : 'text-blue-600'}>{Math.round(proj.progress)}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div 
                      className={`${proj.progress === 100 ? 'bg-emerald-500' : 'bg-blue-500'} h-2 rounded-full transition-all duration-1000 ease-out`} 
                      style={{ width: `${proj.progress}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              
              <div className="px-5 py-3.5 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
                <div className="text-xs text-gray-500 font-semibold flex items-center gap-1.5 bg-white px-2 py-1 rounded border border-gray-200 shadow-sm">
                  <span>{format(new Date(proj.start_date), 'dd/MM/yyyy')}</span>
                  <span className="text-gray-400">→</span>
                  <span className={new Date(proj.end_date) < new Date() && proj.status !== 'completed' ? 'text-red-600' : ''}>
                    {format(new Date(proj.end_date), 'dd/MM/yyyy')}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <button onClick={(e) => { e.stopPropagation(); handlePredictAI(proj); }} className="p-1.5 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-md transition-colors flex items-center gap-1 mr-2 bg-indigo-50/50 border border-indigo-100" title="Phân tích AI tiến độ">
                    <Brain size={16} />
                    <span className="text-xs font-semibold">AI Predict</span>
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); handleOpenModal(proj); }} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors" title="Sửa dự án">
                    <Edit2 size={16} />
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); handleDelete(proj._id); }} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors" title="Xóa dự án">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
            <h2 className="text-xl font-bold mb-4">{editingProject ? 'Sửa Dự án' : 'Thêm Dự án mới'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Tên dự án</label>
                <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Mô tả</label>
                <textarea required rows={3} value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"></textarea>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Ngày bắt đầu</label>
                  <input required type="date" value={formData.start_date} onChange={e => setFormData({...formData, start_date: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Ngày kết thúc</label>
                  <input required type="date" value={formData.end_date} onChange={e => setFormData({...formData, end_date: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Trạng thái</label>
                <select value={formData.status} onChange={e => setFormData({...formData, status: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option value="planning">Lên kế hoạch</option>
                  <option value="in_progress">Đang thực hiện</option>
                  <option value="completed">Đã hoàn thành</option>
                  <option value="delayed">Trễ hạn</option>
                </select>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md font-medium">Hủy</button>
                <button type="submit" className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md font-medium">Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Details Modal */}
      {detailsModalOpen && selectedProject && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
              <h2 className="text-2xl font-bold text-gray-800">{selectedProject.name}</h2>
              <span className={`shrink-0 px-3 py-1 rounded-md text-sm font-bold uppercase tracking-wider
                ${selectedProject.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 
                  selectedProject.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 
                  selectedProject.status === 'delayed' ? 'bg-red-100 text-red-700' : 
                  'bg-gray-100 text-gray-700'}`}>
                {selectedProject.status === 'completed' ? 'Hoàn thành' : 
                 selectedProject.status === 'in_progress' ? 'Đang chạy' : 
                 selectedProject.status === 'delayed' ? 'Trễ hạn' : 'Kế hoạch'}
              </span>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 custom-scrollbar space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Mô tả dự án</h3>
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{selectedProject.description}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                  <div className="text-sm text-gray-500 mb-1 flex items-center gap-1.5"><Clock size={16}/> Thời gian</div>
                  <div className="font-semibold text-gray-800">
                    {format(new Date(selectedProject.start_date), 'dd/MM/yyyy')} - {format(new Date(selectedProject.end_date), 'dd/MM/yyyy')}
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                  <div className="text-sm text-gray-500 mb-1 flex items-center gap-1.5"><Activity size={16}/> Tiến độ tổng quan</div>
                  <div className="font-semibold text-gray-800 flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${selectedProject.progress}%` }}></div>
                    </div>
                    <span>{Math.round(selectedProject.progress)}%</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Thành viên tham gia ({projectMembers.length})</h3>
                {loadingMembers ? (
                  <div className="text-sm text-gray-500 animate-pulse">Đang tải danh sách thành viên...</div>
                ) : projectMembers.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {projectMembers.map((member) => (
                      <div key={member.id} className="flex items-center gap-2 bg-white border border-gray-200 rounded-full px-3 py-1.5 shadow-sm">
                        <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">
                          {member.name.charAt(0)}
                        </div>
                        <span className="text-sm font-medium text-gray-700">{member.name}</span>
                        <span className="text-xs text-gray-400 bg-gray-100 px-1.5 rounded-full">{member.taskCount} tasks</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 italic">Chưa có thành viên nào được phân công.</div>
                )}
              </div>

              <div className="mt-6 border-t border-gray-100 pt-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-semibold text-indigo-600 uppercase tracking-wider flex items-center gap-2">
                    <Brain size={18} /> AI Trợ lý Quản lý Dự án
                  </h3>
                  {!aiPrediction && (
                    <button 
                      onClick={() => handlePredictAI(selectedProject, true)}
                      disabled={isPredicting}
                      className="px-4 py-1.5 text-sm bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-semibold rounded-lg transition-colors disabled:opacity-50"
                    >
                      {isPredicting ? 'Đang phân tích...' : 'Phân tích Dự án'}
                    </button>
                  )}
                </div>
                
                {isPredicting && (
                  <div className="bg-indigo-50/50 rounded-xl p-6 border border-indigo-100 text-center">
                    <Brain className="mx-auto text-indigo-400 animate-bounce mb-3" size={32} />
                    <p className="text-indigo-600 font-medium">AI đang phân tích tiến độ, lịch sử và hiệu suất thành viên...</p>
                  </div>
                )}
                
                {predictError && (
                  <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 text-sm">
                    {predictError}
                  </div>
                )}

                {aiPrediction && (
                  <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-100/50 shadow-sm space-y-4">
                    <div className="flex justify-between items-end mb-2">
                      <div>
                        <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Xác suất hoàn thành đúng hạn</p>
                        <div className="flex items-center gap-3">
                          <span className={`text-4xl font-extrabold ${aiPrediction.completion_probability > 75 ? 'text-emerald-500' : aiPrediction.completion_probability > 40 ? 'text-yellow-500' : 'text-red-500'}`}>
                            {aiPrediction.completion_probability.toFixed(1)}%
                          </span>
                          {aiPrediction.completion_probability > 75 ? (
                            <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs font-bold">AN TOÀN</span>
                          ) : aiPrediction.completion_probability > 40 ? (
                            <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-bold">RỦI RO MỨC VỪA</span>
                          ) : (
                            <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-bold">NGUY CƠ TRỄ HẠN</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="w-full bg-gray-200 rounded-full h-3 mt-4 mb-2">
                      <div 
                        className={`h-3 rounded-full transition-all duration-1000 ${aiPrediction.completion_probability > 75 ? 'bg-emerald-500' : aiPrediction.completion_probability > 40 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                        style={{ width: `${aiPrediction.completion_probability}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 text-right mb-4">Dựa trên mô phỏng 1000 kịch bản tương lai (Monte Carlo)</p>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white/60 p-3 rounded-xl flex items-center gap-3 border border-white">
                        <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                          <Activity size={20} />
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 font-medium">Lượng công việc</p>
                          <p className="font-bold text-gray-800">{aiPrediction.completed_tasks} / {aiPrediction.total_tasks} <span className="text-xs font-normal text-gray-500">tasks</span></p>
                        </div>
                      </div>
                      <div className="bg-white/60 p-3 rounded-xl flex items-center gap-3 border border-white">
                        <div className="bg-purple-100 p-2 rounded-lg text-purple-600">
                          <Clock size={20} />
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 font-medium">Thời gian còn lại</p>
                          <p className="font-bold text-gray-800">{Math.floor(aiPrediction.days_left)} <span className="text-xs font-normal text-gray-500">ngày</span></p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-4 rounded-xl border border-indigo-50 mt-4 shadow-sm">
                      <h4 className="font-semibold text-indigo-800 text-sm mb-2 flex items-center gap-1">
                        <Brain size={16} /> AI Insight:
                      </h4>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        Thuật toán phân tích quá khứ và mô phỏng dự báo rằng tốc độ làm việc hiện tại của team {aiPrediction.completion_probability > 75 ? 'rất lý tưởng' : 'chưa đủ để đáp ứng hạn chót'}. 
                        {aiPrediction.completion_probability < 75 && ' Đề xuất: Cần phân bổ thêm nguồn lực hoặc điều chỉnh lại danh sách tính năng (Scope).'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
              <button 
                onClick={() => setDetailsModalOpen(false)} 
                className="px-5 py-2.5 text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg font-medium transition-colors"
              >
                Đóng
              </button>
              <button 
                onClick={() => {
                  setDetailsModalOpen(false);
                  navigate(`/tasks?project=${selectedProject._id}`);
                }}
                className="px-5 py-2.5 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium shadow-sm flex items-center gap-2 transition-colors"
              >
                <Activity size={18} /> Đi tới Bảng Công Việc
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Modal */}
      {isAiModalOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden border border-gray-100">
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Brain size={24} className="text-indigo-200" />
                  Báo cáo Phân tích AI
                </h2>
                <p className="text-indigo-100 text-sm mt-1">Sử dụng thuật toán Monte Carlo Simulation</p>
              </div>
              <button onClick={() => setIsAiModalOpen(false)} className="text-white hover:bg-white/20 p-2 rounded-full transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            
            <div className="p-6">
              {isPredicting ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
                  <p className="text-gray-500 font-medium">AI đang mô phỏng 1000 kịch bản tương lai...</p>
                </div>
              ) : predictError ? (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg flex gap-3">
                  <AlertTriangle size={20} />
                  <p>{predictError}</p>
                </div>
              ) : aiPrediction ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-gray-800 text-lg">Dự án: {aiPrediction.name}</h3>
                    <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-bold uppercase tracking-wide">
                      Tiến độ: {Math.round(aiPrediction.progress)}%
                    </span>
                  </div>

                  <div className="bg-gray-50 p-6 rounded-xl border border-gray-100">
                    <div className="flex justify-between items-end mb-2">
                      <div>
                        <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Xác suất hoàn thành đúng hạn</p>
                        <div className="flex items-center gap-3">
                          <span className={`text-4xl font-extrabold ${aiPrediction.completion_probability > 75 ? 'text-emerald-500' : aiPrediction.completion_probability > 40 ? 'text-yellow-500' : 'text-red-500'}`}>
                            {aiPrediction.completion_probability.toFixed(1)}%
                          </span>
                          {aiPrediction.completion_probability > 75 ? (
                            <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs font-bold">AN TOÀN</span>
                          ) : aiPrediction.completion_probability > 40 ? (
                            <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-bold">RỦI RO MỨC VỪA</span>
                          ) : (
                            <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-bold">NGUY CƠ TRỄ HẠN</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="w-full bg-gray-200 rounded-full h-3 mt-4 mb-2">
                      <div 
                        className={`h-3 rounded-full transition-all duration-1000 ${aiPrediction.completion_probability > 75 ? 'bg-emerald-500' : aiPrediction.completion_probability > 40 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                        style={{ width: `${aiPrediction.completion_probability}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 text-right">Dựa trên mô phỏng 1000 kịch bản biến động nhân sự</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="border border-gray-100 p-4 rounded-xl flex items-start gap-4">
                      <div className="bg-blue-100 p-3 rounded-lg text-blue-600">
                        <Activity size={24} />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 font-medium">Lượng công việc</p>
                        <p className="text-lg font-bold text-gray-800">{aiPrediction.completed_tasks} / {aiPrediction.total_tasks} <span className="text-sm font-normal text-gray-500">tasks</span></p>
                      </div>
                    </div>
                    <div className="border border-gray-100 p-4 rounded-xl flex items-start gap-4">
                      <div className="bg-purple-100 p-3 rounded-lg text-purple-600">
                        <Clock size={24} />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 font-medium">Thời gian còn lại</p>
                        <p className="text-lg font-bold text-gray-800">{Math.floor(aiPrediction.days_left)} <span className="text-sm font-normal text-gray-500">ngày</span></p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                    <h4 className="font-semibold text-blue-800 text-sm mb-2 flex items-center gap-1">
                      <Brain size={16} /> AI Insight:
                    </h4>
                    <p className="text-sm text-blue-900/80 leading-relaxed">
                      Thuật toán phân tích quá khứ (Historical Velocity) và mô phỏng Monte Carlo dự báo rằng tốc độ làm việc hiện tại của team {aiPrediction.completion_probability > 75 ? 'rất lý tưởng' : 'chưa đủ để đáp ứng hạn chót'}. 
                      {aiPrediction.completion_probability < 75 && ' Đề xuất: Phân bổ thêm nguồn lực hoặc điều chỉnh lại Scope của dự án.'}
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
            
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-100 flex justify-end">
              <button onClick={() => setIsAiModalOpen(false)} className="px-5 py-2.5 text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg font-semibold transition-colors">Đóng báo cáo</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Projects;
