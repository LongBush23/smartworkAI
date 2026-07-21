import { useEffect, useState } from 'react';
import { Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, Brain, Target, TrendingUp, Users, Info, Zap, AlertTriangle } from 'lucide-react';
import api from '../lib/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    projects: 0,
    activeProjects: 0,
    employees: 0,
    tasksDone: 0
  });

  const [aiPerformance, setAiPerformance] = useState<any[]>([]);
  const [aiPrediction, setAiPrediction] = useState<any>(null);
  const [activeProjects, setActiveProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [recommendedTasks, setRecommendedTasks] = useState<any[]>([]);
  const [workloadAnalysis, setWorkloadAnalysis] = useState<any[]>([]);
  const [userRole, setUserRole] = useState('staff');
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [projRes, taskRes, empRes, perfRes, meRes] = await Promise.all([
          api.get('/projects/'),
          api.get('/tasks/'),
          api.get('/employees/'),
          api.get('/ai/performance'),
          api.get('/auth/me')
        ]);

        const projects = projRes.data;
        const tasks = taskRes.data;
        const employees = empRes.data;
        const performance = perfRes.data;
        const user = meRes.data;
        setUserRole(user.role);

        if (user.role === 'staff') {
          api.get('/ai/recommend-tasks').then(res => setRecommendedTasks(res.data)).catch(() => {});
        } else {
          api.get('/ai/workload-analysis').then(res => setWorkloadAnalysis(res.data)).catch(() => {});
        }

        const activeProjs = projects.filter((p: any) => p.status !== 'done');
        setActiveProjects(activeProjs);

        setStats({
          projects: projects.length,
          activeProjects: activeProjs.length,
          employees: employees.length,
          tasksDone: tasks.filter((t: any) => t.status === 'done').length
        });

        // Calculate Clusters for Pie Chart
        const clusters = { 'Giỏi': 0, 'Khá': 0, 'Kém': 0 };
        performance.forEach((p: any) => {
          if (clusters[p.cluster as keyof typeof clusters] !== undefined) {
            clusters[p.cluster as keyof typeof clusters]++;
          }
        });

        const pieData = [
          { name: 'Giỏi', value: clusters['Giỏi'] },
          { name: 'Khá', value: clusters['Khá'] },
          { name: 'Kém', value: clusters['Kém'] }
        ];

        setAiPerformance(pieData);

        // Fetch AI Prediction for the first active project by default
        if (activeProjs.length > 0) {
          setSelectedProjectId(activeProjs[0]._id);
          const predRes = await api.get(`/ai/predict-deadline/${activeProjs[0]._id}`);
          setAiPrediction(predRes.data);
        }

      } catch (error) {
        console.error("Dashboard Error:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const handleSelectProject = async (projectId: string) => {
    setSelectedProjectId(projectId);
    if (!projectId) {
      setAiPrediction(null);
      return;
    }
    try {
      setPredicting(true);
      const predRes = await api.get(`/ai/predict-deadline/${projectId}`);
      setAiPrediction(predRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setPredicting(false);
    }
  };

  const COLORS = ['#10b981', '#3b82f6', '#f43f5e']; // Emerald, Blue, Rose

  if (loading) {
    return <div className="flex h-full items-center justify-center text-gray-500">Đang phân tích dữ liệu AI...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Brain className="text-indigo-600" size={32} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">AI Dashboard</h1>
          <p className="text-sm text-gray-500">Phân tích chuyên sâu & Dự báo tự động</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
            <Target size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Tổng Dự án</p>
            <h3 className="text-2xl font-bold text-gray-900">{stats.projects}</h3>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Đang triển khai</p>
            <h3 className="text-2xl font-bold text-gray-900">{stats.activeProjects}</h3>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600">
            <Users size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Nhân sự</p>
            <h3 className="text-2xl font-bold text-gray-900">{stats.employees}</h3>
          </div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center text-orange-600">
            <TrendingUp size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Task hoàn thành</p>
            <h3 className="text-2xl font-bold text-gray-900">{stats.tasksDone}</h3>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {/* AI Performance Analysis */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Brain size={20} className="text-indigo-500" /> 
            Phân loại Năng lực Nhân sự (AI Cluster)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={aiPerformance}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {aiPerformance.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div className="bg-emerald-50 rounded-lg p-3 text-center border border-emerald-100">
              <span className="block text-emerald-600 font-bold mb-1">Giỏi</span>
              <p className="text-xs text-emerald-800">Hoàn thành task sớm, chất lượng cao</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3 text-center border border-blue-100">
              <span className="block text-blue-600 font-bold mb-1">Khá</span>
              <p className="text-xs text-blue-800">Hoàn thành đúng hạn, chất lượng ổn</p>
            </div>
            <div className="bg-rose-50 rounded-lg p-3 text-center border border-rose-100">
              <span className="block text-rose-600 font-bold mb-1">Kém</span>
              <p className="text-xs text-rose-800">Thường xuyên trễ hạn hoặc làm sai</p>
            </div>
          </div>
          
          <div className="mt-4 flex items-start gap-2 bg-gray-50 p-3 rounded-lg border border-gray-100">
            <Info size={16} className="text-gray-400 shrink-0 mt-0.5" />
            <p className="text-xs text-gray-500 leading-relaxed">AI sử dụng thuật toán <strong className="text-gray-700">K-Means Clustering (Học máy không giám sát)</strong> để tự động phân cụm nhân sự dựa trên 3 chiều dữ liệu: Tỷ lệ đúng hạn, Điểm chất lượng trung bình, và Số lượng task hoàn thành.</p>
          </div>
        </div>

        {/* AI Deadline Prediction */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col h-full min-h-[300px]">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <Activity size={20} className="text-rose-500" /> 
              Dự báo Tiến độ (AI Prediction)
            </h3>
            {activeProjects.length > 0 && (
              <select 
                value={selectedProjectId} 
                onChange={(e) => handleSelectProject(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-2 py-1 outline-none focus:ring-1 focus:ring-rose-500"
              >
                {activeProjects.map(p => (
                  <option key={p._id} value={p._id}>{p.name}</option>
                ))}
              </select>
            )}
          </div>
          
          {predicting ? (
             <div className="flex-1 flex items-center justify-center text-gray-400 text-sm pb-8">
               Đang phân tích...
             </div>
          ) : aiPrediction ? (
            <div className="flex flex-col flex-1 justify-center pb-6">
              <div className="text-center mb-6">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Khả năng hoàn thành đúng hạn</p>
                <div className="relative inline-flex items-center justify-center">
                  <svg className="w-40 h-24" viewBox="0 0 100 50">
                    <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#f3f4f6" strokeWidth="12" strokeLinecap="round" />
                    <path 
                      d="M 10 50 A 40 40 0 0 1 90 50" 
                      fill="none" 
                      stroke={aiPrediction.completion_probability > 75 ? '#10b981' : aiPrediction.completion_probability > 40 ? '#eab308' : '#f43f5e'} 
                      strokeWidth="12" 
                      strokeLinecap="round" 
                      strokeDasharray="125.6" 
                      strokeDashoffset={125.6 - (125.6 * aiPrediction.completion_probability / 100)} 
                      style={{ transition: 'stroke-dashoffset 1.5s ease-out' }}
                    />
                  </svg>
                  <div className="absolute bottom-0 left-0 right-0 text-center">
                    <span className={`text-3xl font-extrabold ${aiPrediction.completion_probability > 75 ? 'text-emerald-500' : aiPrediction.completion_probability > 40 ? 'text-yellow-500' : 'text-rose-500'}`}>
                      {aiPrediction.completion_probability.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm mt-4">
                <div className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center justify-center">
                  <span className="block text-gray-400 text-xs uppercase font-bold mb-1">Thời gian còn lại</span>
                  <span className="text-xl font-bold text-gray-800">{Math.floor(aiPrediction.days_left)} <span className="text-sm font-normal text-gray-500">ngày</span></span>
                </div>
                <div className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center justify-center">
                  <span className="block text-gray-400 text-xs uppercase font-bold mb-1">Task hoàn thành</span>
                  <span className="text-xl font-bold text-gray-800">{aiPrediction.completed_tasks} / {aiPrediction.total_tasks}</span>
                </div>
              </div>
              
              <div className="mt-5 flex items-start gap-2 bg-gray-50 p-3 rounded-lg border border-gray-100">
                <Info size={16} className="text-gray-400 shrink-0 mt-0.5" />
                <p className="text-xs text-gray-500 leading-relaxed">AI chạy <strong className="text-gray-700">Mô phỏng Monte Carlo 1000 kịch bản</strong> tương lai dựa trên tốc độ làm việc (Velocity) lịch sử của team để đưa ra con số dự báo này.</p>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400 pb-8 text-sm">
              Chưa có dữ liệu dự án đang chạy để phân tích.
            </div>
          )}
        </div>
      </div>
      
      {/* AI Recommendations for Staff */}
      {userRole === 'staff' && (
        <div className="mt-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Brain size={24} className="text-indigo-600" />
            Công việc AI gợi ý cho bạn
          </h3>
          {recommendedTasks.length === 0 ? (
            <div className="bg-white p-6 rounded-xl border border-gray-100 text-gray-500 text-sm text-center">
              Hiện không có gợi ý công việc nào.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recommendedTasks.map((rec: any) => (
                <div key={rec.task._id} className="bg-white p-6 rounded-xl shadow-sm border border-indigo-100 relative overflow-hidden group hover:shadow-md transition-shadow">
                  <div className="absolute top-0 right-0 bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg z-10 shadow-sm">
                    Khớp: {rec.match_score}%
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2 truncate pr-16">{rec.task.title}</h4>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{rec.task.description}</p>
                  <div className="bg-indigo-50/50 p-3 rounded-lg border border-indigo-100 mb-4 text-xs text-indigo-900 leading-relaxed">
                    <span className="font-bold flex items-center gap-1 mb-1 text-indigo-700"><Zap size={14} /> AI giải thích: </span>{rec.reasoning}
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex justify-between text-xs font-bold text-gray-500 mb-1">
                      <span>Độ phù hợp</span>
                      <span className="text-indigo-600">{rec.match_score}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${rec.match_score}%` }}></div>
                    </div>
                  </div>

                  <div className="flex gap-1.5 text-[10px] font-bold text-gray-500 mb-4 flex-wrap uppercase tracking-wider">
                    {rec.task.required_skills?.map((s: string) => (
                      <span key={s} className="bg-gray-100 px-2 py-1 rounded-md border border-gray-200">{s}</span>
                    ))}
                  </div>
                  <button onClick={() => window.location.href = '/tasks'} className="w-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold py-2 rounded-lg text-sm transition-colors border border-indigo-200">
                    Xem chi tiết & Xin nhận
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Workload Analysis for Managers */}
      {['leader', 'director', 'admin'].includes(userRole) && (
        <div className="mt-8 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Activity size={24} className="text-orange-500" />
            Cảnh báo Workload & Burnout
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Nhân viên</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Giờ làm việc (Tuần)</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Hiệu suất sử dụng</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Cảnh báo Burnout</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {workloadAnalysis.map((item: any) => (
                  <tr key={item._id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.current_workload} / {item.capacity}h</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-gray-200 rounded-full h-2 max-w-[100px]">
                          <div 
                            className={`h-2 rounded-full ${item.utilization_percent > 90 ? 'bg-red-500' : item.utilization_percent > 70 ? 'bg-orange-500' : 'bg-emerald-500'}`} 
                            style={{ width: `${Math.min(item.utilization_percent, 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500">{item.utilization_percent}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-sm">
                      <span className={`px-3 py-1.5 rounded-md text-xs font-bold flex inline-flex items-center gap-1.5 ${
                        item.burnout_risk.includes('Nguy hiểm') ? 'bg-rose-100 text-rose-800 border border-rose-200 animate-pulse shadow-sm' : 
                        item.burnout_risk.includes('Cao') ? 'bg-orange-100 text-orange-800 border border-orange-200' : 
                        'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      }`}>
                        {item.burnout_risk.includes('Nguy hiểm') && <AlertTriangle size={14} className="text-rose-600" />}
                        {item.burnout_risk}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
