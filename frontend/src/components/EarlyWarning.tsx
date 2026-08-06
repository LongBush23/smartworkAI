import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, TrendingDown, Clock, Info, Lock } from 'lucide-react';
import { aiApi } from '../lib/ai-api';
import type { OfficerRisk, TaskRisk } from '../lib/ai-api';

/**
 * Khối cảnh báo sớm cho lãnh đạo, chỉ huy.
 *
 * Đây là dự báo để đôn đốc, hỗ trợ kịp thời — KHÔNG phải kết quả đánh giá và
 * không ảnh hưởng tới điểm KPI của bất kỳ ai.
 */
export const EarlyWarning = ({ departmentId }: { departmentId?: string }) => {
  const [officers, setOfficers] = useState<OfficerRisk[]>([]);
  const [tasks, setTasks] = useState<TaskRisk[]>([]);
  const [unusable, setUnusable] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { load(); }, [departmentId]);

  const load = async () => {
    setLoading(true);
    setFailed(false);
    setUnusable(null);

    // Gọi riêng từng cái để một bên hỏng không làm mất kết quả của bên kia,
    // và để phân biệt "không có cảnh báo" với "không tải được"
    const [o, t] = await Promise.allSettled([
      aiApi.officerRisk({ department_id: departmentId, threshold: 0.5 }),
      aiApi.taskRisk({ department_id: departmentId, threshold: 0.5 }),
    ]);

    if (o.status === 'fulfilled') {
      if (!o.value.usable) setUnusable(o.value.reason ?? 'Mô hình chưa đủ dữ liệu');
      setOfficers(o.value.items ?? []);
    } else {
      setFailed(true);
      setOfficers([]);
    }

    if (t.status === 'fulfilled') {
      setTasks(t.value.items ?? []);
    } else {
      setFailed(true);
      setTasks([]);
    }

    setLoading(false);
  };

  if (loading) {
    return (
      <div className="bg-white border border-navy-200 rounded-sm p-6 flex justify-center">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-navy-600" />
      </div>
    );
  }

  if (unusable) {
    return (
      <div className="bg-white border border-navy-200 rounded-sm p-4">
        <p className="section-label mb-1">Cảnh báo sớm</p>
        <p className="text-xs text-navy-500">{unusable}</p>
      </div>
    );
  }

  const nothing = officers.length === 0 && tasks.length === 0;

  return (
    <div className="bg-white border border-navy-200 rounded-sm overflow-hidden">
      <div className="px-4 py-2 border-b border-navy-200 bg-navy-50 flex items-center justify-between">
        <p className="section-label flex items-center gap-1.5">
          <AlertTriangle size={13} className="text-crimson-700" /> Cảnh báo sớm
        </p>
        {!nothing && (
          <span className="text-[11px] text-navy-500 tabular">
            {officers.length} cán bộ · {tasks.length} nhiệm vụ
          </span>
        )}
      </div>

      {failed ? (
        <div className="p-6 text-center">
          <p className="text-sm text-crimson-700 font-medium">Không tải được cảnh báo</p>
          <p className="text-xs text-navy-500 mt-1">
            Máy chủ hoặc cơ sở dữ liệu đang không phản hồi. Đây không có nghĩa là
            không có cảnh báo nào.
          </p>
          <button
            onClick={load}
            className="mt-3 px-3 py-1.5 border border-navy-300 rounded-sm text-xs text-navy-700 hover:bg-navy-50"
          >
            Thử lại
          </button>
        </div>
      ) : nothing ? (
        <p className="p-8 text-center text-sm text-navy-500">
          Chưa có cảnh báo nào trong kỳ này.
        </p>
      ) : (
        <div className="divide-y divide-navy-100">
          {officers.length > 0 && (
            <div className="p-4">
              <p className="text-xs font-medium text-navy-700 flex items-center gap-1.5 mb-2">
                <TrendingDown size={13} className="text-crimson-600" />
                Nguy cơ rơi Nhóm 3 khi kết thúc kỳ
              </p>
              <div className="space-y-2">
                {officers.slice(0, 5).map(o => (
                  <div key={o.officer_id} className="flex items-start justify-between gap-3 bg-crimson-50/50 border border-crimson-100 rounded-sm px-3 py-2">
                    <div className="min-w-0">
                      <Link to={`/employees/${o.officer_id}`} className="text-sm font-medium text-navy-800 hover:underline">
                        {o.name}
                      </Link>
                      <p className="text-[11px] text-navy-500">{o.rank_position}</p>
                      <p className="text-[11px] text-navy-600 mt-0.5">
                        Đã xong {o.tasks_done}/{o.tasks_total} việc
                        {o.tasks_overdue > 0 && ` · ${o.tasks_overdue} quá hạn`}
                        {o.recent_kpi != null && ` · KPI trước ${o.recent_kpi}`}
                      </p>
                      <p className="text-[10px] text-navy-400 mt-0.5">{o.reasons.join(' · ')}</p>
                    </div>
                    <span className="shrink-0 text-sm font-bold text-crimson-700 tabular">
                      {(o.probability * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tasks.length > 0 && (
            <div className="p-4">
              <p className="text-xs font-medium text-navy-700 flex items-center gap-1.5 mb-2">
                <Clock size={13} className="text-gold-600" />
                Nhiệm vụ có nguy cơ trễ hạn
              </p>
              <div className="space-y-2">
                {tasks.slice(0, 6).map(t => (
                  <div key={t.task_id} className="flex items-start justify-between gap-3 bg-gold-50/60 border border-gold-100 rounded-sm px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm text-navy-800 flex items-center gap-1.5">
                        {t.classification !== 'thuong' && <Lock size={11} className="text-crimson-600 shrink-0" />}
                        <span className="font-mono text-[11px] text-navy-500">{t.code}</span>
                        {t.classification === 'thuong' && (
                          <span className="truncate">{t.title}</span>
                        )}
                      </p>
                      <p className="text-[11px] text-navy-600 mt-0.5">
                        {t.assignee_name}
                        {t.days_left != null && (
                          t.days_left < 0 ? ` · đã trễ ${Math.abs(t.days_left)} ngày` : ` · còn ${t.days_left} ngày`
                        )}
                        {t.reminder_count > 0 && ` · đã nhắc ${t.reminder_count} lần`}
                      </p>
                    </div>
                    <span className="shrink-0 text-sm font-bold text-gold-700 tabular">
                      {(t.probability * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="px-4 py-2 border-t border-navy-100 bg-navy-50/50 flex items-start gap-1.5">
        <Info size={11} className="text-navy-400 shrink-0 mt-0.5" />
        <p className="text-[10px] text-navy-500 leading-relaxed">
          Dự báo để đôn đốc, hỗ trợ kịp thời. Đây <strong>không phải</strong> kết quả đánh giá
          và không ảnh hưởng tới điểm KPI. Nhiệm vụ có độ mật chỉ hiển thị mã hiệu.
        </p>
      </div>
    </div>
  );
};
