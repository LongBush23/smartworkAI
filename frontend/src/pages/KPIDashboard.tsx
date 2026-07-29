import { useEffect, useState } from 'react';
import { kpiApi } from '../lib/kpi-api';
import type { KPIRankingItem } from '../lib/kpi-api';
import { Target, Users, Activity, Medal, Star, AlertCircle } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { KPI_GROUP_LABELS, KPI_GROUP_COLORS, ROLE_LABELS } from '../lib/kpi-api';

const KPIDashboard = () => {
  const [ranking, setRanking] = useState<KPIRankingItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const currentYear = new Date().getFullYear();
        const rankingRes = await kpiApi.getRanking({ period_year: currentYear });
        setRanking(rankingRes);
      } catch (error) {
        console.error('Failed to fetch KPI dashboard data', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  const topPerformers = [...ranking].sort((a, b) => b.kpi_score - a.kpi_score).slice(0, 5);
  
  const groupStats = {
    group_1: ranking.filter(r => r.kpi_group === 'group_1').length,
    group_2: ranking.filter(r => r.kpi_group === 'group_2').length,
    group_3: ranking.filter(r => r.kpi_group === 'group_3').length,
  };

  const chartData = [
    { name: 'Nhóm 1', full: 'Nhóm 1 – Đáp ứng tốt', count: groupStats.group_1, fill: '#10b981' },
    { name: 'Nhóm 2', full: 'Nhóm 2 – Đáp ứng', count: groupStats.group_2, fill: '#3b82f6' },
    { name: 'Nhóm 3', full: 'Nhóm 3 – Chưa đáp ứng', count: groupStats.group_3, fill: '#ef4444' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Tổng quan KPI (Năm {new Date().getFullYear()})</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Tổng đánh giá</p>
              <h3 className="text-3xl font-bold text-gray-800 mt-1">{ranking.length}</h3>
            </div>
            <div className="p-3 bg-indigo-50 rounded-lg">
              <Users className="h-6 w-6 text-indigo-600" />
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Nhóm 1 – Đáp ứng tốt</p>
              <p className="text-xs text-gray-400 mt-0.5">KPI 70 – 100</p>
              <h3 className="text-3xl font-bold text-green-600 mt-1">{groupStats.group_1}</h3>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <Star className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Nhóm 2 – Đáp ứng</p>
              <p className="text-xs text-gray-400 mt-0.5">KPI 50 – dưới 70</p>
              <h3 className="text-3xl font-bold text-blue-600 mt-1">{groupStats.group_2}</h3>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Target className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Nhóm 3 – Chưa đáp ứng</p>
              <p className="text-xs text-gray-400 mt-0.5">KPI dưới 50</p>
              <h3 className="text-3xl font-bold text-red-600 mt-1">{groupStats.group_3}</h3>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <AlertCircle className="h-6 w-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-6 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-indigo-600" />
            Phân bố Xếp loại KPI
          </h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" interval={0} />
                <YAxis />
                <Tooltip
                  cursor={{ fill: '#f3f4f6' }}
                  formatter={(v) => [`${v} lượt đánh giá`, 'Số lượng']}
                  labelFormatter={(label) =>
                    chartData.find(d => d.name === label)?.full ?? String(label)
                  }
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-6 flex items-center">
            <Medal className="h-5 w-5 mr-2 text-amber-500" />
            Bảng vàng thành tích
          </h2>
          <div className="space-y-4">
            {topPerformers.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Chưa có dữ liệu đánh giá</p>
            ) : (
              topPerformers.map((user, index) => (
                <div key={user.target_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold mr-4 ${
                      index === 0 ? 'bg-amber-100 text-amber-600' :
                      index === 1 ? 'bg-gray-200 text-gray-600' :
                      index === 2 ? 'bg-orange-100 text-orange-600' : 'bg-indigo-50 text-indigo-600'
                    }`}>
                      #{index + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">{user.target_name}</p>
                      <p className="text-xs text-gray-500">{ROLE_LABELS[user.role ?? ''] ?? user.role}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg text-indigo-600">{user.kpi_score.toFixed(1)} <span className="text-xs font-normal text-gray-500">điểm</span></p>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full inline-block mt-1 ${KPI_GROUP_COLORS[user.kpi_group] ?? 'text-gray-600 bg-gray-100'}`}>
                      {KPI_GROUP_LABELS[user.kpi_group] ?? user.kpi_group}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default KPIDashboard;
