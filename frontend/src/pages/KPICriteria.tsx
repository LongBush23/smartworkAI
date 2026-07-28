import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { ClipboardCheck, Save, Check, X, Info } from 'lucide-react';
import api from '../lib/api';
import { kpiApi } from '../lib/kpi-api';
import type { CriteriaTemplate, CriteriaItem, KPIEvaluation } from '../lib/kpi-api';

type CriteriaType = 'collective' | 'leader' | 'staff';

const TYPE_LABELS: Record<CriteriaType, string> = {
  collective: 'Tập thể',
  leader: 'Cá nhân là lãnh đạo, chỉ huy',
  staff: 'Cá nhân không là lãnh đạo, chỉ huy',
};

/** Tiêu chí lá (đơn vị được chấm điểm) — mục có sub_criteria thì lấy các sub */
function flatten(criteria: CriteriaItem[]) {
  return criteria.flatMap(c =>
    c.sub_criteria?.length
      ? c.sub_criteria.map(s => ({ ...s, parent: c.name }))
      : [{ id: c.id, name: c.name, max_score: c.max_score, parent: undefined as string | undefined }]
  );
}

const KPICriteria = () => {
  const [me, setMe] = useState<any>(null);
  const [templates, setTemplates] = useState<Record<string, CriteriaTemplate>>({});
  const [type, setType] = useState<CriteriaType>('staff');
  const [evaluations, setEvaluations] = useState<KPIEvaluation[]>([]);
  const [selectedEvalId, setSelectedEvalId] = useState('');
  // criteria_id → đảm bảo / không đảm bảo
  const [ratings, setRatings] = useState<Record<string, boolean>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const year = new Date().getFullYear();

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      setLoading(true);
      const [meRes, tmplList, evals] = await Promise.all([
        api.get('/auth/me'),
        kpiApi.getAllCriteriaTemplates(),
        kpiApi.getEvaluations({ period_year: year }).catch(() => []),
      ]);
      setMe(meRes.data);
      setTemplates(Object.fromEntries(tmplList.map(t => [t.type, t])));
      // Chỉ chấm tiêu chí chung sau khi đã xác định điểm KPI (Bước 3)
      setEvaluations(evals.filter(e => e.overall_status === 'approved'));
    } catch (error) {
      console.error('Không tải được khung tiêu chí chung', error);
      toast.error('Không tải được khung tiêu chí chung');
    } finally {
      setLoading(false);
    }
  };

  const template = templates[type];
  const leaves = template ? flatten(template.criteria) : [];

  // Khi chọn kỳ đánh giá, tự chọn bộ tiêu chí phù hợp và nạp điểm đã chấm
  const handleSelectEval = (id: string) => {
    setSelectedEvalId(id);
    const ev = evaluations.find(e => e.id === id);
    if (!ev) return;

    const inferred: CriteriaType = ev.evaluation_type === 'collective'
      ? 'collective'
      : (ev.target_role === 'leader' || ev.target_role === 'director') ? 'leader' : 'staff';
    setType(inferred);

    const existing = ev.general_criteria?.scores as any[] | undefined;
    if (existing?.length) {
      setRatings(Object.fromEntries(existing.map(s => [s.criteria_id, s.rating === 'dam_bao'])));
      setNotes(Object.fromEntries(existing.filter(s => s.note).map(s => [s.criteria_id, s.note])));
      toast.success('Đã nạp kết quả chấm điểm trước đó');
    } else {
      // Mặc định coi là đảm bảo, người chấm bỏ tích với tiêu chí không đảm bảo
      const tmpl = templates[inferred];
      setRatings(Object.fromEntries(flatten(tmpl?.criteria ?? []).map(l => [l.id, true])));
      setNotes({});
    }
  };

  const totalE = leaves.reduce((sum, l) => sum + (ratings[l.id] ? l.max_score : 0), 0);
  const maxE = template?.total_max_score ?? 30;

  const selectedEval = evaluations.find(e => e.id === selectedEvalId);
  const kpiScore = selectedEval?.approval?.kpi_score != null ? Number(selectedEval.approval.kpi_score) : null;
  const finalScore = kpiScore != null ? totalE + kpiScore * 0.7 : null;

  const handleSave = async () => {
    if (!selectedEvalId) { toast.error('Chưa chọn kỳ đánh giá'); return; }
    try {
      setSaving(true);
      await kpiApi.submitGeneralCriteria(selectedEvalId, {
        criteria_type: type,
        scores: leaves.map(l => ({
          criteria_id: l.id,
          criteria_name: l.name,
          max_score: l.max_score,
          rating: ratings[l.id] ? 'dam_bao' : 'khong_dam_bao',
          actual_score: ratings[l.id] ? l.max_score : 0,
          note: notes[l.id] || undefined,
        })),
      });
      toast.success('Đã lưu điểm tiêu chí chung');
      load();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Không lưu được điểm tiêu chí chung');
    } finally {
      setSaving(false);
    }
  };

  const canScore = ['leader', 'director', 'admin'].includes(me?.role);

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <ClipboardCheck className="h-6 w-6 text-blue-600" />
          Tiêu chí chung (Điểm E)
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Khung tiêu chí đánh giá theo Phụ lục Hướng dẫn số 20-HD/ĐUCA — tối đa 30 điểm.
        </p>
      </div>

      {/* Chọn kỳ đánh giá + bộ tiêu chí */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Kỳ đánh giá đã xác định điểm KPI
            </label>
            <select
              value={selectedEvalId}
              onChange={e => handleSelectEval(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">— Chọn kỳ đánh giá —</option>
              {evaluations.map(e => (
                <option key={e.id} value={e.id}>
                  {e.evaluation_type === 'collective' ? '[Tập thể] ' : ''}
                  {e.target_name} · {e.period_month ? `Tháng ${e.period_month}/` : ''}{e.period_year}
                  {e.general_criteria ? ' ✓ đã chấm' : ''}
                </option>
              ))}
            </select>
            {evaluations.length === 0 && (
              <p className="text-xs text-amber-700 mt-1">
                Chưa có kỳ nào hoàn tất Bước 3. Cần xác định điểm KPI trước khi chấm tiêu chí chung.
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bộ tiêu chí áp dụng</label>
            <select
              value={type}
              onChange={e => {
                const t = e.target.value as CriteriaType;
                setType(t);
                setRatings(Object.fromEntries(flatten(templates[t]?.criteria ?? []).map(l => [l.id, true])));
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              {(Object.keys(TYPE_LABELS) as CriteriaType[]).map(t => (
                <option key={t} value={t}>{TYPE_LABELS[t]}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Tổng hợp điểm */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-5 border-t border-gray-100">
          <div>
            <p className="text-xs text-gray-500">Điểm tiêu chí chung (E)</p>
            <p className="text-2xl font-bold text-blue-700 mt-0.5">{totalE}<span className="text-sm text-gray-400">/{maxE}</span></p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Điểm KPI của kỳ</p>
            <p className="text-2xl font-bold text-indigo-700 mt-0.5">{kpiScore != null ? kpiScore.toFixed(1) : '–'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">KPI × 0,7</p>
            <p className="text-2xl font-bold text-gray-700 mt-0.5">{kpiScore != null ? (kpiScore * 0.7).toFixed(1) : '–'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Tổng điểm xếp loại</p>
            <p className="text-2xl font-bold text-amber-700 mt-0.5">{finalScore != null ? finalScore.toFixed(1) : '–'}</p>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-3 flex items-start gap-1.5">
          <Info size={13} className="mt-0.5 shrink-0" />
          Tổng điểm = E + KPI × 0,7 &nbsp;(F đối với tập thể, G đối với cá nhân, H đối với lãnh đạo, chỉ huy).
        </p>
      </div>

      {/* Bảng chấm điểm */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="font-semibold text-gray-800">{template?.name}</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Tiêu chí đảm bảo được chấm tối đa số điểm; không đảm bảo chấm 0 điểm.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-white border-b border-gray-200 text-gray-600">
                <th className="p-3 font-medium w-12 text-center">TT</th>
                <th className="p-3 font-medium">Tiêu chí / nội dung</th>
                <th className="p-3 font-medium text-center w-20">Điểm tối đa</th>
                <th className="p-3 font-medium text-center w-32">Đánh giá</th>
                <th className="p-3 font-medium text-center w-20">Điểm đạt</th>
                <th className="p-3 font-medium w-48">Ghi chú</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {leaves.flatMap((l, idx) => {
                const ok = !!ratings[l.id];
                const prevParent = idx > 0 ? leaves[idx - 1].parent : undefined;
                const showParent = l.parent && l.parent !== prevParent;
                return [
                    showParent ? (
                      <tr key={`${l.id}-group`} className="bg-gray-50">
                        <td colSpan={6} className="px-3 py-2 text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          {l.parent}
                        </td>
                      </tr>
                    ) : null,
                    <tr key={l.id} className="hover:bg-gray-50 align-top">
                      <td className="p-3 text-center text-gray-400 text-xs">{idx + 1}</td>
                      <td className="p-3 text-gray-700 leading-relaxed">{l.name}</td>
                      <td className="p-3 text-center font-medium text-gray-700">{l.max_score}</td>
                      <td className="p-3">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            disabled={!canScore}
                            onClick={() => setRatings({ ...ratings, [l.id]: true })}
                            className={`p-1.5 rounded transition ${ok ? 'bg-green-100 text-green-700' : 'text-gray-300 hover:bg-gray-100'} disabled:cursor-not-allowed`}
                            title="Đảm bảo"
                          >
                            <Check size={16} />
                          </button>
                          <button
                            disabled={!canScore}
                            onClick={() => setRatings({ ...ratings, [l.id]: false })}
                            className={`p-1.5 rounded transition ${!ok ? 'bg-red-100 text-red-700' : 'text-gray-300 hover:bg-gray-100'} disabled:cursor-not-allowed`}
                            title="Không đảm bảo"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      </td>
                      <td className={`p-3 text-center font-bold ${ok ? 'text-green-700' : 'text-red-600'}`}>
                        {ok ? l.max_score : 0}
                      </td>
                      <td className="p-3">
                        <input
                          disabled={!canScore}
                          value={notes[l.id] ?? ''}
                          onChange={e => setNotes({ ...notes, [l.id]: e.target.value })}
                          placeholder="—"
                          className="w-full px-2 py-1 border border-gray-200 rounded text-xs disabled:bg-gray-50"
                        />
                      </td>
                    </tr>,
                ];
              })}
            </tbody>
            <tfoot>
              <tr className="bg-gray-50 border-t-2 border-gray-200 font-bold text-gray-800">
                <td className="p-3" />
                <td className="p-3">Tổng điểm</td>
                <td className="p-3 text-center">{maxE}</td>
                <td className="p-3" />
                <td className="p-3 text-center text-blue-700">{totalE}</td>
                <td className="p-3" />
              </tr>
            </tfoot>
          </table>
        </div>

        {canScore && (
          <div className="px-5 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving || !selectedEvalId}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              <Save size={16} /> {saving ? 'Đang lưu…' : 'Lưu điểm tiêu chí chung'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default KPICriteria;
