import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { ShieldAlert, RefreshCw, Info, ChevronDown, ChevronRight } from 'lucide-react';
import api from '../lib/api';
import { aiApi, SEVERITY_LABELS, SEVERITY_COLORS } from '../lib/ai-api';
import type { AnomalyResult } from '../lib/ai-api';

const QualityReview = () => {
  const now = new Date();
  const [period, setPeriod] = useState({ month: now.getMonth() + 1, year: now.getFullYear() });
  const [data, setData] = useState<AnomalyResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState<any>(null);
  const [retraining, setRetraining] = useState(false);
  const [showThresholds, setShowThresholds] = useState(false);

  useEffect(() => { load(); }, [period.month, period.year]);

  const load = async () => {
    try {
      setLoading(true);
      const [meRes, result] = await Promise.all([
        api.get('/auth/me'),
        aiApi.anomalies({ period_month: period.month, period_year: period.year }),
      ]);
      setMe(meRes.data);
      setData(result);
    } catch (error) {
      console.error('Không tải được kết quả rà soát', error);
      toast.error('Không tải được kết quả rà soát');
    } finally {
      setLoading(false);
    }
  };

  const handleRetrain = async () => {
    try {
      setRetraining(true);
      const r = await aiApi.retrain();
      const late = r.task_late, g3 = r.group3;
      toast.success(
        `Đã huấn luyện lại · Trễ hạn AUC ${late.auc ?? '—'} · Nhóm 3 AUC ${g3.auc ?? '—'}`,
        { duration: 6000 },
      );
    } catch {
      toast.error('Không huấn luyện lại được');
    } finally {
      setRetraining(false);
    }
  };

  const selectClass = 'px-2.5 py-1.5 border border-navy-200 rounded-sm text-xs bg-white text-navy-700';

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-600" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 justify-between items-start">
        <div>
          <h1 className="text-xl font-bold text-navy-900 flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-crimson-700" /> Rà soát chất lượng đánh giá
          </h1>
          <p className="text-xs text-navy-500 mt-0.5">
            Dấu hiệu chấm điểm hình thức, thiếu thực chất — để xem lại, không phải kết luận vi phạm.
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <select value={period.month} onChange={e => setPeriod({ ...period, month: parseInt(e.target.value) })} className={selectClass}>
            {[...Array(12)].map((_, i) => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <select value={period.year} onChange={e => setPeriod({ ...period, year: parseInt(e.target.value) })} className={selectClass}>
            {[...Array(5)].map((_, i) => {
              const y = now.getFullYear() - 2 + i;
              return <option key={y} value={y}>{y}</option>;
            })}
          </select>
          {me?.role === 'admin' && (
            <button
              onClick={handleRetrain}
              disabled={retraining}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-navy-300 text-navy-700 rounded-sm hover:bg-navy-50 text-xs disabled:opacity-50"
            >
              <RefreshCw size={13} className={retraining ? 'animate-spin' : ''} />
              {retraining ? 'Đang huấn luyện…' : 'Huấn luyện lại mô hình'}
            </button>
          )}
        </div>
      </div>

      {/* Tổng hợp */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Kỳ đánh giá đã rà soát', value: data?.total_evaluations ?? 0, color: 'text-navy-900' },
          { label: 'Cần rà soát ngay', value: data?.summary.cao ?? 0, color: (data?.summary.cao ?? 0) > 0 ? 'text-crimson-700' : 'text-navy-300' },
          { label: 'Nên xem lại', value: data?.summary.trung_binh ?? 0, color: (data?.summary.trung_binh ?? 0) > 0 ? 'text-gold-600' : 'text-navy-300' },
          { label: 'Ghi nhận', value: data?.summary.thap ?? 0, color: 'text-navy-600' },
        ].map(s => (
          <div key={s.label} className="bg-white border border-navy-200 rounded-sm p-3">
            <p className="section-label leading-tight">{s.label}</p>
            <p className={`text-2xl font-bold tabular mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Danh sách dấu hiệu */}
      <div className="bg-white border border-navy-200 rounded-sm overflow-hidden">
        <div className="px-4 py-2 border-b border-navy-200 bg-navy-50">
          <p className="section-label">Dấu hiệu phát hiện được</p>
        </div>

        {!data || data.flags.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-sm text-navy-600 font-medium">
              Không phát hiện dấu hiệu bất thường trong kỳ này.
            </p>
            <p className="text-xs text-navy-400 mt-1">
              Đã rà soát {data?.total_evaluations ?? 0} kỳ đánh giá thuộc {data?.departments_reviewed ?? 0} đơn vị.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-navy-100">
            {data.flags.map((f, i) => (
              <div key={i} className="p-4 hover:bg-navy-50/40">
                <div className="flex items-start gap-3">
                  <span className={`shrink-0 px-2 py-0.5 text-[10px] font-medium rounded-sm border ${SEVERITY_COLORS[f.severity]}`}>
                    {SEVERITY_LABELS[f.severity]}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-navy-800 text-sm">{f.title}</p>
                    <p className="text-xs text-navy-600 mt-0.5">
                      <span className="font-medium">{f.target}</span> — {f.evidence}
                    </p>
                    <p className="text-xs text-navy-500 mt-1.5 italic">{f.suggestion}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Ngưỡng áp dụng — công khai để người đọc tự thẩm định */}
      <div className="bg-white border border-navy-200 rounded-sm">
        <button
          onClick={() => setShowThresholds(!showThresholds)}
          className="w-full px-4 py-2.5 flex items-center justify-between text-left hover:bg-navy-50/50"
        >
          <span className="section-label">Ngưỡng áp dụng khi rà soát</span>
          {showThresholds ? <ChevronDown size={15} className="text-navy-400" /> : <ChevronRight size={15} className="text-navy-400" />}
        </button>
        {showThresholds && (
          <div className="px-4 pb-4 overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="text-navy-500 border-b border-navy-100">
                  <th className="text-left py-1.5 font-medium">Dấu hiệu</th>
                  <th className="text-left py-1.5 font-medium">Bật cờ khi</th>
                </tr>
              </thead>
              <tbody className="text-navy-700">
                {[
                  ['Điểm tiêu chí chung đồng loạt tối đa', '≥ 80% cán bộ đơn vị đạt 30/30'],
                  ['Điểm KPI quá đồng đều', 'độ lệch chuẩn trong đơn vị < 3 điểm'],
                  ['Tự đánh giá lệch thẩm định', 'tự nhận cách kết quả ≥ 2 nhóm'],
                  ['Điểm KPI nhảy vọt', 'chênh ≥ 10 điểm VÀ gấp > 2 lần dao động thường thấy'],
                  ['Mâu thuẫn quá hạn và xếp loại', '> 30% việc quá hạn nhưng không ai Nhóm 3'],
                  ['Bỏ qua đơn vị nhỏ', 'dưới 4 cán bộ thì thống kê vô nghĩa, không xét'],
                ].map(([a, b]) => (
                  <tr key={a} className="border-b border-navy-50">
                    <td className="py-1.5 pr-4">{a}</td>
                    <td className="py-1.5 text-navy-500">{b}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex items-start gap-2 text-[11px] text-navy-500 bg-navy-50 border border-navy-200 rounded-sm px-3 py-2">
        <Info size={13} className="shrink-0 mt-0.5" />
        <p>{data?.explanation}</p>
      </div>
    </div>
  );
};

export default QualityReview;
