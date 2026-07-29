import { useState, useEffect } from 'react';
import { kpiApi } from '../lib/kpi-api';
import type { KPIRankingItem } from '../lib/kpi-api';
import { Award, FileBarChart, Filter } from 'lucide-react';
import { KPI_GROUP_LABELS, KPI_GROUP_COLORS, ROLE_LABELS } from '../lib/kpi-api';

const KPIResults = () => {
  const [ranking, setRanking] = useState<KPIRankingItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [filterPeriod, setFilterPeriod] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1
  });

  useEffect(() => {
    fetchData();
  }, [filterPeriod.year, filterPeriod.month]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await kpiApi.getRanking({ 
        period_year: filterPeriod.year,
        period_month: filterPeriod.month
      });
      setRanking(res);
    } catch (error) {
      console.error('Failed to fetch KPI results', error);
    } finally {
      setLoading(false);
    }
  };

  const getGroupName = (group: string) => KPI_GROUP_LABELS[group] ?? group;
  const getGroupColor = (group: string) => KPI_GROUP_COLORS[group] ?? 'text-gray-700 bg-gray-100 border-gray-200';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center">
          <Award className="h-6 w-6 mr-2 text-indigo-600" />
          Kết quả Đánh giá KPI
        </h1>
        
        <div className="flex items-center space-x-4 bg-white p-2 rounded-lg border border-gray-200 shadow-sm">
          <Filter className="h-4 w-4 text-gray-400 ml-2" />
          <select 
            className="bg-transparent border-none focus:ring-0 text-sm font-medium text-gray-700"
            value={filterPeriod.month}
            onChange={(e) => setFilterPeriod({...filterPeriod, month: parseInt(e.target.value)})}
          >
            {[...Array(12)].map((_, i) => (
              <option key={i+1} value={i+1}>Tháng {i+1}</option>
            ))}
          </select>
          <div className="w-px h-4 bg-gray-300"></div>
          <select 
            className="bg-transparent border-none focus:ring-0 text-sm font-medium text-gray-700 pr-4"
            value={filterPeriod.year}
            onChange={(e) => setFilterPeriod({...filterPeriod, year: parseInt(e.target.value)})}
          >
            {[...Array(5)].map((_, i) => {
              const year = new Date().getFullYear() - 2 + i;
              return <option key={year} value={year}>Năm {year}</option>;
            })}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex items-center">
          <FileBarChart className="h-5 w-5 mr-2 text-gray-500" />
          <h2 className="font-semibold text-gray-700">Chi tiết Bảng điểm</h2>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>
        ) : ranking.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            Chưa có kết quả đánh giá nào được phê duyệt cho kỳ này.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="p-4 font-medium text-gray-600 text-sm whitespace-nowrap">Đối tượng</th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center">Điểm A<br/><span className="text-xs text-gray-400 font-normal">(Số lượng)</span></th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center">Điểm B<br/><span className="text-xs text-gray-400 font-normal">(Chất lượng)</span></th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center">Điểm C<br/><span className="text-xs text-gray-400 font-normal">(Tiến độ)</span></th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center">Điểm D<br/><span className="text-xs text-gray-400 font-normal">(Lãnh đạo)</span></th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center bg-indigo-50">Điểm KPI</th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center">Điểm E<br/><span className="text-xs text-gray-400 font-normal">(Tiêu chí chung)</span></th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center bg-amber-50">Tổng điểm<br/><span className="text-xs text-gray-400 font-normal">(E + KPI*0.7)</span></th>
                  <th className="p-4 font-medium text-gray-600 text-sm text-center">Xếp loại</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ranking.map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4">
                      <div className="font-medium text-gray-900">{item.target_name}</div>
                      {item.role && (
                        <div className="text-xs text-gray-500">{ROLE_LABELS[item.role] ?? item.role}</div>
                      )}
                    </td>
                    <td className="p-4 text-center text-sm font-medium text-gray-700">{item.score_A ? (item.score_A * 100).toFixed(1) + '%' : '-'}</td>
                    <td className="p-4 text-center text-sm font-medium text-gray-700">{item.score_B ? (item.score_B * 100).toFixed(1) + '%' : '-'}</td>
                    <td className="p-4 text-center text-sm font-medium text-gray-700">{item.score_C ? (item.score_C * 100).toFixed(1) + '%' : '-'}</td>
                    <td className="p-4 text-center text-sm font-medium text-gray-700">{item.score_D !== null && item.score_D !== undefined ? (item.score_D * 100).toFixed(1) + '%' : '-'}</td>
                    <td className="p-4 text-center text-base font-bold text-indigo-700 bg-indigo-50/50">{item.kpi_score.toFixed(1)}</td>
                    <td className="p-4 text-center text-sm font-medium text-gray-700">{item.total_E !== null && item.total_E !== undefined ? item.total_E.toFixed(1) : '-'}</td>
                    <td className="p-4 text-center text-base font-bold text-amber-700 bg-amber-50/50">
                      {item.total_final_score !== null && item.total_final_score !== undefined ? item.total_final_score.toFixed(1) : '-'}
                    </td>
                    <td className="p-4 text-center">
                      <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${getGroupColor(item.kpi_group)}`}>
                        {getGroupName(item.kpi_group)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex">
        <div className="flex-shrink-0 mt-0.5">
          <svg className="h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-blue-800">Công thức tính điểm KPI (Hướng dẫn số 20-HD/ĐUCA)</h3>
          <div className="mt-2 text-sm text-blue-700 space-y-1">
            <p><strong>A</strong> = Σ(điểm CV đã hoàn thành) / Σ(điểm CV được giao theo Danh mục)</p>
            <p><strong>B</strong> = Σ(điểm chất lượng CV đã HT) / Σ(điểm CV được giao) &nbsp;|&nbsp; <strong>C</strong> = Σ(điểm tiến độ CV đã HT) / Σ(điểm CV được giao)</p>
            <p><strong>D</strong> = Tỷ lệ tập thể/cá nhân thuộc quyền hoàn thành NV (chỉ áp dụng với lãnh đạo, chỉ huy)</p>
            <hr className="border-blue-200 my-1" />
            <p><strong>KPI tập thể / cá nhân không là lãnh đạo</strong> = (A + B + C) / 3 × 100</p>
            <p><strong>KPI cá nhân là lãnh đạo, chỉ huy</strong> = (A + B + C + D) / 4 × 100</p>
            <p className="text-xs text-blue-600 mt-1">KPI người đứng đầu ≤ KPI tập thể do mình đứng đầu</p>
            <hr className="border-blue-200 my-1" />
            <p><strong>E</strong> = Điểm tiêu chí chung (tối đa 30 điểm)</p>
            <p><strong>F</strong> (tập thể) = <strong>G</strong> (cá nhân) = <strong>H</strong> (lãnh đạo) = E + KPI × 0,7</p>
            <p className="text-xs text-blue-600 mt-1">
              Nhóm 1 (KPI 70–100) &nbsp;|&nbsp; Nhóm 2 (KPI 50–dưới 70) &nbsp;|&nbsp; Nhóm 3 (KPI dưới 50)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KPIResults;
