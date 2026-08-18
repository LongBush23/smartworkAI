import { useState, useEffect } from 'react';
import { kpiApi } from '../lib/kpi-api';
import type { KPIEvaluation, TaskKPIScore } from '../lib/kpi-api';
import { Check, ClipboardList, Send, ChevronRight } from 'lucide-react';
import { GuidelineLookup } from '../components/GuidelineLookup';
import { KhungMoHinh } from '../components/KhungMoHinh';
import { layMe } from '../lib/me';

const STEP_LABELS = [
  'Tự đánh giá và đề xuất mức xếp loại',
  'Cơ quan có liên quan thẩm định, đề xuất',
  'Cấp có thẩm quyền xác định điểm KPI',
];

const QUALITY_OPTIONS = [
  { value: 'excellent', label: 'Vượt mức yêu cầu (≤120%)' },
  { value: 'good',      label: 'Đảm bảo chất lượng (100%)' },
  { value: 'fair_1',    label: 'Cơ bản đảm bảo – sửa 1 lần (≤75%)' },
  { value: 'fair_2_4',  label: 'Còn thiếu sót – sửa 2-4 lần (≤50%)' },
  { value: 'poor_5_6',  label: 'Nhiều thiếu sót – sửa 5-6 lần (≤25%)' },
  { value: 'fail_7',    label: 'Không đạt – sửa ≥7 lần (0%)' },
];

const TIMELINE_OPTIONS = [
  { value: 'ahead',   label: 'Vượt tiến độ và đảm bảo chất lượng (≤120%)' },
  { value: 'on_time', label: 'Đúng tiến độ và đảm bảo chất lượng (100%)' },
  { value: 'late_1',  label: 'Chưa đảm bảo tiến độ – nhắc nhở 1 lần (≤75%)' },
  { value: 'late_2',  label: 'Chưa đảm bảo tiến độ – nhắc nhở 2 lần (≤50%)' },
  { value: 'late_3',  label: 'Chưa đảm bảo tiến độ – nhắc nhở 3 lần (≤25%)' },
  { value: 'fail_4',  label: 'Nhắc nhở ≥4 lần (0%)' },
];

const RATING_OPTIONS = [
  { value: 'group_1', label: 'Nhóm 1 – Đáp ứng tốt yêu cầu nhiệm vụ (KPI 70–100)' },
  { value: 'group_2', label: 'Nhóm 2 – Đáp ứng yêu cầu nhiệm vụ (KPI 50–dưới 70)' },
  { value: 'group_3', label: 'Nhóm 3 – Chưa đáp ứng yêu cầu nhiệm vụ (KPI dưới 50)' },
];

function getStatusStep(status: string): number {
  if (status === 'draft') return 0;
  if (status === 'self_evaluating') return 1;
  if (status === 'reviewing') return 2;
  return 3;
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    draft:           { label: 'Chưa tự đánh giá',              cls: 'bg-gray-100 text-gray-600' },
    self_evaluating: { label: 'Bước 1 – Chờ thẩm định',        cls: 'bg-blue-100 text-blue-700' },
    reviewing:       { label: 'Bước 2 – Chờ xác định điểm KPI', cls: 'bg-amber-100 text-amber-700' },
    approved:        { label: 'Bước 3 – Đã xác định điểm KPI', cls: 'bg-green-100 text-green-700' },
  };
  const { label, cls } = map[status] ?? { label: status, cls: 'bg-gray-100 text-gray-600' };
  return <span className={`text-xs px-2 py-1 rounded-full font-medium ${cls}`}>{label}</span>;
}

const KPIEvaluate = () => {
  const [evaluations, setEvaluations] = useState<KPIEvaluation[]>([]);
  const today = new Date();
  const [period, setPeriod] = useState({ month: today.getMonth() + 1, year: today.getFullYear() });
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState('staff');
  const [userId, setUserId] = useState('');

  const [selectedEval, setSelectedEval] = useState<KPIEvaluation | null>(null);
  const [taskScores, setTaskScores] = useState<TaskKPIScore[]>([]);
  const [proposedRating, setProposedRating] = useState('group_2');
  const [reviewNote, setReviewNote] = useState('');

  useEffect(() => { fetchData(); }, [period.month, period.year]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const meRes = { data: await layMe() };
      setUserRole(meRes.data.role);
      setUserId(meRes.data._id);
      const evals = await kpiApi.getEvaluations({
        period_month: period.month,
        period_year: period.year,
      });
      setEvaluations(evals);
    } catch (error) {
      console.error('Failed to fetch evaluations', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEval = async (id: string) => {
    try {
      const detail = await kpiApi.getEvaluation(id);
      setSelectedEval(detail);
      if (detail.review?.task_scores) {
        setTaskScores(detail.review.task_scores);
      } else if (detail.self_evaluation?.task_scores) {
        setTaskScores(detail.self_evaluation.task_scores);
        setProposedRating(detail.self_evaluation.proposed_rating ?? 'group_2');
      } else {
        setTaskScores([
          { task_id: 'task1', task_name: 'Xây dựng kế hoạch công tác', kpi_point: 50, is_completed: true, quality_tier: 'good', timeline_tier: 'on_time' }
        ]);
      }
    } catch (error) {
      console.error('Failed to load evaluation details', error);
    }
  };

  const updateTaskScore = (index: number, field: string, value: unknown) => {
    const newScores = [...taskScores];
    newScores[index] = { ...newScores[index], [field]: value };
    setTaskScores(newScores);
  };

  const submitSelfEval = async () => {
    if (!selectedEval) return;
    try {
      await kpiApi.submitSelfEvaluation(selectedEval.id, { task_scores: taskScores, proposed_rating: proposedRating });
      alert('Đã gửi Bước 1 – Tự đánh giá. Chờ cơ quan có liên quan thẩm định (Bước 2).');
      setSelectedEval(null);
      fetchData();
    } catch { alert('Lỗi gửi tự đánh giá'); }
  };

  const submitReview = async () => {
    if (!selectedEval) return;
    try {
      await kpiApi.submitReview(selectedEval.id, { task_scores: taskScores, review_note: reviewNote });
      alert('Đã hoàn tất Bước 2 – Thẩm định. Chờ cấp có thẩm quyền xác định điểm KPI (Bước 3).');
      setSelectedEval(null);
      fetchData();
    } catch { alert('Lỗi chấm điểm'); }
  };

  const approveEval = async (id: string) => {
    try {
      await kpiApi.approveEvaluation(id);
      alert('Đã hoàn tất Bước 3 – Cấp có thẩm quyền đã xác định điểm KPI.');
      fetchData();
    } catch { alert('Lỗi phê duyệt'); }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3 justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Quy trình Tính điểm KPI</h1>
        <div className="flex items-center gap-2">
          <select
            value={period.month}
            onChange={e => setPeriod({ ...period, month: parseInt(e.target.value) })}
            className="px-3 py-1.5 border border-gray-300 rounded-sm text-sm bg-white"
          >
            {[...Array(12)].map((_, i) => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <select
            value={period.year}
            onChange={e => setPeriod({ ...period, year: parseInt(e.target.value) })}
            className="px-3 py-1.5 border border-gray-300 rounded-sm text-sm bg-white"
          >
            {[...Array(5)].map((_, i) => {
              const y = today.getFullYear() - 2 + i;
              return <option key={y} value={y}>{y}</option>;
            })}
          </select>
        </div>
      </div>

      {/* Sơ đồ 3 bước */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <p className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wide">
          Quy trình theo Hướng dẫn số 20-HD/ĐUCA
        </p>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          {STEP_LABELS.map((label, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold shrink-0">
                  {i + 1}
                </div>
                <p className="text-sm text-gray-700">{label}</p>
              </div>
              {i < 2 && <ChevronRight className="h-4 w-4 text-gray-400 hidden sm:block shrink-0" />}
            </div>
          ))}
        </div>
      </div>

      <KhungMoHinh ma="tra_cuu_huong_dan">
        <GuidelineLookup />
      </KhungMoHinh>

      {!selectedEval ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200 bg-gray-50 font-semibold text-gray-700 flex items-center">
            <ClipboardList className="h-5 w-5 mr-2" /> Danh sách kỳ đánh giá
          </div>
          <div className="divide-y divide-gray-100">
            {evaluations.length === 0 ? (
              <div className="p-8 text-center text-gray-500">Không có kỳ đánh giá nào.</div>
            ) : (
              evaluations.map(ev => (
                <div key={ev.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                  <div>
                    <h3 className="font-semibold text-indigo-700">
                      {ev.period_month ? `Tháng ${ev.period_month}/` : ''}{ev.period_year}
                    </h3>
                    <p className="text-sm text-gray-600 mt-0.5">
                      {ev.evaluation_type === 'individual' ? 'Cá nhân' : 'Tập thể'}: {ev.target_name}
                    </p>
                    <div className="mt-1.5">
                      <StatusBadge status={ev.overall_status} />
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 items-end">
                    {ev.overall_status === 'draft' && ev.target_id === userId && (
                      <button onClick={() => handleSelectEval(ev.id)} className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700">
                        Bước 1 – Tự đánh giá
                      </button>
                    )}
                    {ev.overall_status === 'self_evaluating' && (userRole === 'leader' || userRole === 'director') && (
                      <button onClick={() => handleSelectEval(ev.id)} className="px-3 py-1.5 bg-amber-600 text-white rounded text-sm hover:bg-amber-700">
                        Bước 2 – Thẩm định
                      </button>
                    )}
                    {ev.overall_status === 'reviewing' && userRole === 'director' && (
                      <button onClick={() => approveEval(ev.id)} className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                        Bước 3 – Xác định điểm KPI
                      </button>
                    )}
                    {ev.overall_status === 'approved' && ev.approval && (
                      <div className="text-right">
                        <p className="text-lg font-bold text-indigo-700">{Number(ev.approval.kpi_score).toFixed(1)} điểm</p>
                        <p className="text-xs text-gray-500">KPI đã xác định</p>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
            <div>
              <h2 className="font-semibold text-gray-800">
                Bước {getStatusStep(selectedEval.overall_status) + 1} – {STEP_LABELS[getStatusStep(selectedEval.overall_status)]}
              </h2>
              <p className="text-sm text-gray-500 mt-0.5">Đối tượng: {selectedEval.target_name}</p>
            </div>
            <button onClick={() => setSelectedEval(null)} className="text-gray-500 hover:text-gray-700 text-sm">
              Quay lại
            </button>
          </div>

          <div className="p-6">
            <h3 className="font-medium text-gray-700 mb-1">Danh mục nhiệm vụ công tác</h3>
            <p className="text-xs text-gray-500 mb-4">
              Chấm điểm số lượng (A), chất lượng (B), tiến độ (C) cho từng công việc theo Danh mục nhiệm vụ.
            </p>

            <div className="space-y-4">
              {taskScores.map((ts, idx) => (
                <div key={idx} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={ts.is_completed}
                        onChange={(e) => updateTaskScore(idx, 'is_completed', e.target.checked)}
                        className="w-4 h-4 rounded border-gray-300"
                      />
                      <span className="font-medium text-gray-800">{ts.task_name}</span>
                    </div>
                    <span className="text-indigo-600 font-bold shrink-0 ml-2">{ts.kpi_point} điểm</span>
                  </div>

                  {ts.is_completed && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Chất lượng (B) – số lần sửa chữa
                        </label>
                        <select
                          className="w-full p-2 border rounded border-gray-300 text-sm"
                          value={ts.quality_tier}
                          onChange={(e) => updateTaskScore(idx, 'quality_tier', e.target.value)}
                        >
                          {QUALITY_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Tiến độ (C) – số lần nhắc nhở
                        </label>
                        <select
                          className="w-full p-2 border rounded border-gray-300 text-sm"
                          value={ts.timeline_tier}
                          onChange={(e) => updateTaskScore(idx, 'timeline_tier', e.target.value)}
                        >
                          {TIMELINE_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="mt-8 border-t pt-6">
              {selectedEval.overall_status === 'draft' ? (
                <div>
                  <label className="block font-medium text-gray-700 mb-2">
                    Tự nhận xét và đề xuất mức xếp loại:
                  </label>
                  <select
                    className="w-full sm:w-2/3 p-2 border rounded border-gray-300 mb-4 text-sm"
                    value={proposedRating}
                    onChange={(e) => setProposedRating(e.target.value)}
                  >
                    {RATING_OPTIONS.map(o => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                  <div className="flex justify-end">
                    <button onClick={submitSelfEval} className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
                      <Send className="w-4 h-4 mr-2" /> Gửi tự đánh giá (Bước 1)
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <label className="block font-medium text-gray-700 mb-2">
                    Nhận xét và đề xuất của cơ quan thẩm định (Bước 2):
                  </label>
                  <textarea
                    className="w-full p-3 border rounded border-gray-300 mb-4 h-24 text-sm"
                    placeholder="Nhập nhận xét, đề xuất của cơ quan có liên quan thẩm định..."
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                  />
                  <div className="flex justify-end">
                    <button onClick={submitReview} className="flex items-center px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700">
                      <Check className="w-4 h-4 mr-2" /> Hoàn tất thẩm định – chuyển Bước 3
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KPIEvaluate;
