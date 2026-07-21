import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Plus, MoreHorizontal, User as UserIcon, Calendar, ChevronDown, ChevronRight, X, Search } from 'lucide-react';
import { format } from 'date-fns';
import { useSearchParams } from 'react-router-dom';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import type { DropResult } from '@hello-pangea/dnd';
import toast from 'react-hot-toast';
import { TaskModal } from '../components/TaskModal';

interface Task {
  _id: string;
  project_id: string;
  title: string;
  description: string;
  assigned_to: string | null;
  status: string;
  progress: number;
  deadline: string;
  actual_end: string | null;
  effort_required: number;
}

interface User {
  _id: string;
  name: string;
}

interface Project {
  _id: string;
  name: string;
}

const Tasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [userSearchTerm, setUserSearchTerm] = useState('');
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [searchParams] = useSearchParams();
  const [expandedProjects, setExpandedProjects] = useState<string[]>([]);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  // Time Log State
  const [isTimeLogModalOpen, setIsTimeLogModalOpen] = useState(false);
  const [timeLogHours, setTimeLogHours] = useState('');
  const [timeLogs, setTimeLogs] = useState<any[]>([]);


  const [formData, setFormData] = useState({
    title: '',
    description: '',
    project_id: '',
    assigned_to: '',
    status: 'todo',
    deadline: new Date().toISOString().split('T')[0],
    effort_required: 1
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [tasksRes, usersRes, projsRes, meRes] = await Promise.all([
        api.get('/tasks/'),
        api.get('/employees/'),
        api.get('/projects/'),
        api.get('/auth/me')
      ]);
      
      const tasksData = tasksRes.data;
      const projsData = projsRes.data;
      const currentUser = meRes.data;

      // Sắp xếp ưu tiên: Dự án có task của user hiện tại lên đầu
      const sortedProjs = projsData.sort((a: any, b: any) => {
        const aHasMyTask = tasksData.some((t: any) => t.project_id === a._id && t.assigned_to === currentUser._id);
        const bHasMyTask = tasksData.some((t: any) => t.project_id === b._id && t.assigned_to === currentUser._id);
        if (aHasMyTask && !bHasMyTask) return -1;
        if (!aHasMyTask && bHasMyTask) return 1;
        return 0;
      });

      setTasks(tasksData);
      setUsers(usersRes.data);
      setProjects(sortedProjs);
      
      const targetProject = searchParams.get('project');
      if (targetProject) {
        setExpandedProjects([targetProject]);
        
        // Scroll to the project accordion after render
        setTimeout(() => {
          const element = document.getElementById(`project-${targetProject}`);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 300);
      } else {
        setExpandedProjects([]); // Mặc định đóng tất cả
      }
    } catch (err) {
      console.error(err);
      toast.error('Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenModal = (task?: Task) => {
    if (task) {
      setEditingTask(task);
      setFormData({
        title: task.title,
        description: task.description,
        project_id: task.project_id,
        assigned_to: task.assigned_to || '',
        status: task.status,
        deadline: task.deadline.split('T')[0],
        effort_required: task.effort_required || 1
      });
    } else {
      setEditingTask(null);
      setFormData({
        title: '',
        description: '',
        project_id: projects.length > 0 ? projects[0]._id : '',
        assigned_to: '',
        status: 'todo',
        deadline: new Date().toISOString().split('T')[0],
        effort_required: 1
      });
    }
    setIsModalOpen(true);
  };

  const handleSaveTask = async (taskData: any) => {
    try {
      const payload = {
        ...taskData,
        progress: taskData.status === 'done' ? 100 : (taskData.status === 'todo' ? 0 : 50)
      };

      if (editingTask) {
        await api.put(`/tasks/${editingTask._id}`, payload);
        toast.success('Đã cập nhật công việc');
      } else {
        await api.post('/tasks/', payload);
        toast.success('Đã tạo công việc mới');
      }
      setIsModalOpen(false);
      fetchData();
    } catch (err) {
      console.error(err);
      toast.error('Lỗi lưu công việc');
    }
  };

  const handleDeleteTask = async (id: string) => {
    if (window.confirm('Xóa công việc này?')) {
      try {
        await api.delete(`/tasks/${id}`);
        setIsModalOpen(false);
        toast.success('Đã xóa công việc');
        fetchData();
      } catch (err) {
        toast.error('Lỗi xóa công việc');
      }
    }
  };



  const fetchTimeLogs = async (taskId: string) => {
    try {
      const res = await api.get(`/timelogs/?task_id=${taskId}`);
      setTimeLogs(res.data);
    } catch (err) {
      console.error(err);
    }
  };


  const handleSaveTimeLog = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTask) return;
    try {
      await api.post('/timelogs/', {
        task_id: editingTask._id,
        user_id: formData.assigned_to || 'unassigned',
        hours: parseFloat(timeLogHours)
      });
      setTimeLogHours('');
      fetchTimeLogs(editingTask._id);
      toast.success('Đã ghi nhận giờ làm!');
    } catch (err) {
      console.error(err);
      toast.error('Lỗi ghi nhận giờ làm');
    }
  };

  const getUserName = (id: string | null) => {
    if (!id) return 'Chưa phân công';
    const user = users.find(u => u._id === id);
    return user ? user.name : 'Unknown';
  };


  const onDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const newStatus = destination.droppableId;
    
    // Optimistic UI update
    setTasks(prevTasks => prevTasks.map(t => {
      if (t._id === draggableId) {
        return { ...t, status: newStatus, progress: newStatus === 'done' ? 100 : (newStatus === 'todo' ? 0 : 50) };
      }
      return t;
    }));

    try {
      const taskToUpdate = tasks.find(t => t._id === draggableId);
      if (taskToUpdate) {
        const payload = {
          ...taskToUpdate,
          status: newStatus,
          progress: newStatus === 'done' ? 100 : (newStatus === 'todo' ? 0 : 50)
        };
        // Remove _id from payload before sending to API
        const { _id, ...rest } = payload;
        await api.put(`/tasks/${_id}`, rest);
        toast.success(`Đã chuyển sang: ${newStatus}`);
      }
    } catch (error) {
      console.error(error);
      toast.error('Lỗi khi chuyển trạng thái');
      fetchData(); // revert UI on error
    }
  };

  const columns = [
    { id: 'todo', title: 'Cần làm', color: 'bg-gray-100', dot: 'bg-gray-400' },
    { id: 'in_progress', title: 'Đang làm', color: 'bg-blue-50', dot: 'bg-blue-500' },
    { id: 'review', title: 'Chờ duyệt', color: 'bg-yellow-50', dot: 'bg-yellow-500' },
    { id: 'done', title: 'Hoàn thành', color: 'bg-emerald-50', dot: 'bg-emerald-500' }
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 shrink-0 gap-4">
        <h1 className="text-2xl font-bold text-gray-800">Bảng Công việc (Kanban)</h1>
        <div className="flex items-center gap-4">
          <div className="relative">
            <div 
              className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm cursor-text min-w-[280px] max-w-[500px] flex-wrap"
              onClick={() => setIsUserDropdownOpen(true)}
            >
              <Search size={16} className="text-gray-400 shrink-0" />
              {selectedUserIds.map(uid => {
                const u = users.find(x => x._id === uid);
                return u ? (
                  <span key={uid} className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-md flex items-center gap-1 font-semibold">
                    {u.name}
                    <X size={14} className="cursor-pointer hover:text-blue-900 bg-blue-100 rounded-full p-0.5" onClick={(e) => { e.stopPropagation(); setSelectedUserIds(prev => prev.filter(id => id !== uid)); }} />
                  </span>
                ) : null;
              })}
              <input 
                type="text" 
                placeholder={selectedUserIds.length === 0 ? "Tìm và lọc theo người dùng..." : ""} 
                value={userSearchTerm}
                onChange={(e) => { setUserSearchTerm(e.target.value); setIsUserDropdownOpen(true); }}
                onFocus={() => setIsUserDropdownOpen(true)}
                className="text-sm outline-none bg-transparent font-medium text-gray-700 flex-1 min-w-[80px]"
              />
            </div>
            
            {isUserDropdownOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setIsUserDropdownOpen(false)}></div>
                <div className="absolute top-full mt-2 left-0 w-full bg-white border border-gray-200 shadow-xl rounded-xl py-2 z-20 max-h-64 overflow-y-auto custom-scrollbar">
                  {users.filter(u => u.name.toLowerCase().includes(userSearchTerm.toLowerCase())).map(u => (
                    <div 
                      key={u._id} 
                      className="px-4 py-2 hover:bg-gray-50 cursor-pointer flex items-center justify-between text-sm"
                      onClick={() => {
                        if (!selectedUserIds.includes(u._id)) {
                          setSelectedUserIds([...selectedUserIds, u._id]);
                        } else {
                          setSelectedUserIds(selectedUserIds.filter(id => id !== u._id));
                        }
                        setUserSearchTerm('');
                        setIsUserDropdownOpen(false); // Optionally close on select, but keeping it open might be better for multi-select. Let's keep it open, so remove this line. Actually keeping focus is good.
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 font-bold text-xs uppercase">
                          {u.name.charAt(0)}
                        </div>
                        <span className="font-medium text-gray-700">{u.name}</span>
                      </div>
                      {selectedUserIds.includes(u._id) && <span className="text-blue-600 font-bold">✓</span>}
                    </div>
                  ))}
                  {users.filter(u => u.name.toLowerCase().includes(userSearchTerm.toLowerCase())).length === 0 && (
                    <div className="px-4 py-3 text-sm text-gray-500 text-center">Không tìm thấy người dùng</div>
                  )}
                </div>
              </>
            )}
          </div>
          <button 
            onClick={() => handleOpenModal()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-medium shadow-sm transition-colors"
          >
            <Plus size={20} />
            <span>Thêm Công việc</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10">Đang tải...</div>
      ) : (
        <div className="flex-1 overflow-y-auto pr-2 pb-10 space-y-4">
          {projects.map(project => {
            const isExpanded = expandedProjects.includes(project._id);
            const projectTasks = tasks.filter(t => t.project_id === project._id);
            const filteredProjectTasks = projectTasks.filter(t => {
              if (selectedUserIds.length === 0) return true;
              return selectedUserIds.includes(t.assigned_to || '');
            });
            
            // Ẩn dự án nếu filter người dùng mà dự án không có task nào của người đó
            if (selectedUserIds.length > 0 && filteredProjectTasks.length === 0) return null;
            
            return (
              <div key={project._id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div 
                  className="bg-gray-50 px-5 py-4 border-b border-gray-200 flex items-center justify-between cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => setExpandedProjects(prev => isExpanded ? prev.filter(id => id !== project._id) : [...prev, project._id])}
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? <ChevronDown size={20} className="text-gray-500" /> : <ChevronRight size={20} className="text-gray-500" />}
                    <h2 className="font-bold text-lg text-gray-800">{project.name}</h2>
                    <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2.5 py-1 rounded-full">
                      {projectTasks.length} tasks
                    </span>
                  </div>
                </div>
                
                {isExpanded && (
                  <div className="p-5 overflow-x-auto custom-scrollbar">
                    <DragDropContext onDragEnd={onDragEnd}>
                      <div className="flex gap-6 pb-2 min-w-max">
                        {columns.map(col => {
                          const colTasks = projectTasks.filter(t => 
                            t.status === col.id && 
                            (selectedUserIds.length === 0 || selectedUserIds.includes(t.assigned_to || ''))
                          );
                          return (
                            <div key={col.id} className={`${col.color} rounded-xl min-w-[300px] w-[300px] p-4 flex flex-col shrink-0 border border-gray-100`}>
                              <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                  <div className={`w-2 h-2 rounded-full ${col.dot}`}></div>
                                  <h3 className="font-semibold text-gray-800">{col.title}</h3>
                                  <span className="bg-white border border-gray-200 text-gray-700 text-xs font-bold px-2 py-0.5 rounded-full shadow-sm">
                                    {colTasks.length}
                                  </span>
                                </div>
                                <button className="text-gray-400 hover:text-gray-700 transition-colors">
                                  <MoreHorizontal size={18} />
                                </button>
                              </div>
                              
                              <Droppable droppableId={col.id}>
                                {(provided) => (
                                  <div 
                                    {...provided.droppableProps}
                                    ref={provided.innerRef}
                                    className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar min-h-[100px]"
                                  >
                                    {colTasks.map((task, index) => (
                                      <Draggable key={task._id} draggableId={task._id} index={index}>
                                        {(provided, snapshot) => (
                                          <div 
                                            ref={provided.innerRef}
                                            {...provided.draggableProps}
                                            {...provided.dragHandleProps}
                                            onClick={() => handleOpenModal(task)}
                                            className={`bg-white p-4 rounded-lg shadow-sm border ${snapshot.isDragging ? 'border-blue-500 shadow-md rotate-2 ring-4 ring-blue-50' : 'border-gray-200 hover:shadow-md hover:border-blue-300'} transition-all cursor-grab active:cursor-grabbing group`}
                                          >
                                            <h4 className="font-semibold text-gray-800 mb-3 leading-snug group-hover:text-blue-700">{task.title}</h4>
                                            
                                            <div className="mt-4 flex items-center justify-between text-xs font-medium">
                                              <div className="flex items-center gap-1.5 text-gray-600 bg-gray-50 px-2 py-1 rounded border border-gray-100">
                                                <UserIcon size={14} className="text-gray-400" />
                                                <span className="truncate max-w-[120px]">{getUserName(task.assigned_to)}</span>
                                              </div>
                                              <div className={`flex items-center gap-1.5 ${new Date(task.deadline) < new Date() && task.status !== 'done' ? 'text-red-600 bg-red-50 px-2 py-1 rounded border border-red-100' : 'text-gray-500'}`}>
                                                <Calendar size={14} />
                                                <span>{format(new Date(task.deadline), 'dd/MM')}</span>
                                              </div>
                                            </div>
                                          </div>
                                        )}
                                      </Draggable>
                                    ))}
                                    {provided.placeholder}
                                  </div>
                                )}
                              </Droppable>
                            </div>
                          );
                        })}
                      </div>
                    </DragDropContext>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <TaskModal 
        isOpen={isModalOpen} 
        task={editingTask} 
        projects={projects} 
        users={users} 
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveTask}
        onDelete={handleDeleteTask}
      />

      {/* Time Log Modal */}
      {isTimeLogModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold mb-4">Nhật ký Giờ làm (Time Logs)</h2>
            <form onSubmit={handleSaveTimeLog} className="flex gap-2 mb-4">
              <input required type="number" step="0.5" min="0.5" placeholder="Số giờ (vd: 2.5)" value={timeLogHours} onChange={e => setTimeLogHours(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" />
              <button type="submit" className="px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700">Lưu Log</button>
            </form>
            
            <div className="max-h-48 overflow-y-auto mb-4 border border-gray-100 rounded-md p-2">
              {timeLogs.length === 0 ? <p className="text-sm text-gray-500 text-center py-4">Chưa có ghi nhận nào.</p> : timeLogs.map(log => (
                <div key={log._id} className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0 text-sm">
                  <span className="text-gray-600">{format(new Date(log.log_date), 'dd/MM/yyyy HH:mm')}</span>
                  <span className="font-semibold text-emerald-600">+{log.hours}h</span>
                </div>
              ))}
            </div>

            <div className="flex justify-end">
              <button onClick={() => setIsTimeLogModalOpen(false)} className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md font-medium text-sm">Đóng</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;
