import { useState, useRef, useEffect } from 'react';
import {
  MessageCircleQuestion, X, Send, FileText, ChevronDown, ChevronRight, Bot, Database,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { aiApi } from '../lib/ai-api';
import type { GuidelineClause } from '../lib/ai-api';
import { troLyApi, NHAN_CONG_CU } from '../lib/tro-ly-api';
import type { TraLoiTroLy, LuotTruoc } from '../lib/tro-ly-api';

/**
 * Trợ lý hỏi đáp, mở được ở mọi trang.
 *
 * Hỏi gì cũng đi qua /api/tro-ly/hoi. Máy chủ chọn công cụ để lấy số liệu rồi
 * mới diễn đạt lại — nên câu trả lời bám đúng dữ liệu người hỏi có quyền xem.
 * Thiếu khoá hoặc dịch vụ trục trặc thì tự lui về máy tra cứu tại chỗ, hộp chat
 * nói rõ đang ở chế độ nào chứ không giấu.
 */

const GOI_Y = [
  'Tôi còn mấy việc quá hạn?',
  'KPI của tôi năm nay thế nào?',
  'Sửa 3 lần thì tính bao nhiêu phần trăm?',
  'Quy trình đánh giá gồm mấy bước?',
];

interface Luot {
  hoi: string;
  dap: TraLoiTroLy | null;
  loi?: boolean;
}

export const HopTraCuu = () => {
  const [mo, setMo] = useState(false);
  const [q, setQ] = useState('');
  const [lich, setLich] = useState<Luot[]>([]);
  const [dangHoi, setDangHoi] = useState(false);

  const [dieuKhoan, setDieuKhoan] = useState<GuidelineClause[] | null>(null);
  const [moDanhMuc, setMoDanhMuc] = useState(false);
  const [dangXem, setDangXem] = useState<string | null>(null);

  const cuoiRef = useRef<HTMLDivElement>(null);
  const oNhapRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (mo) oNhapRef.current?.focus(); }, [mo]);
  useEffect(() => {
    cuoiRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [lich, dangHoi]);
  useEffect(() => {
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setMo(false); };
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, []);

  const hoi = async (cauHoi: string) => {
    const c = cauHoi.trim();
    if (!c || dangHoi) return;
    setQ('');
    setDangHoi(true);

    // Gửi kèm vài lượt gần nhất để trợ lý hiểu câu hỏi nối tiếp
    const lichSu: LuotTruoc[] = [];
    for (const l of lich.slice(-3)) {
      lichSu.push({ vai: 'user', text: l.hoi });
      if (l.dap) lichSu.push({ vai: 'model', text: l.dap.tra_loi });
    }

    try {
      const dap = await troLyApi.hoi(c, lichSu);
      setLich(l => [...l, { hoi: c, dap }]);
    } catch {
      setLich(l => [...l, { hoi: c, dap: null, loi: true }]);
    } finally {
      setDangHoi(false);
    }
  };

  const xemDanhMuc = async () => {
    if (moDanhMuc) { setMoDanhMuc(false); return; }
    setMoDanhMuc(true);
    if (dieuKhoan) return;
    try { setDieuKhoan(await aiApi.allClauses()); } catch { setDieuKhoan([]); }
  };

  if (!mo) {
    return (
      <button
        onClick={() => setMo(true)}
        title="Hỏi trợ lý"
        className="fixed bottom-5 right-5 z-40 h-12 w-12 rounded-full bg-navy-700 text-white
                   shadow-lg shadow-navy-900/30 flex items-center justify-center
                   hover:bg-navy-800 transition-colors"
      >
        <MessageCircleQuestion size={22} />
      </button>
    );
  }

  return (
    <div
      className="fixed z-40 bg-white border border-navy-300 shadow-2xl shadow-navy-900/25
                 flex flex-col rounded-sm
                 inset-x-3 bottom-3 top-16
                 sm:inset-x-auto sm:top-auto sm:right-5 sm:bottom-5 sm:w-[420px] sm:h-[600px]"
    >
      <div className="h-12 shrink-0 bg-navy-700 text-white flex items-center px-3 gap-2">
        <Bot size={17} className="shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-semibold leading-tight">Trợ lý hệ thống</p>
          <p className="text-[10px] text-navy-200 leading-tight truncate">
            Hỏi về nhiệm vụ, điểm KPI và Hướng dẫn 20-HD/ĐUCA
          </p>
        </div>
        <button onClick={() => setMo(false)} className="text-navy-200 hover:text-white shrink-0">
          <X size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3">
        {lich.length === 0 && (
          <div className="space-y-3">
            <p className="text-xs text-navy-600 leading-relaxed">
              Hỏi về nhiệm vụ và điểm KPI của đồng chí, hoặc về cách tính điểm theo Hướng dẫn.
              Trợ lý chỉ đọc được dữ liệu trong phạm vi đồng chí có quyền xem.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {GOI_Y.map(s => (
                <button key={s} onClick={() => hoi(s)}
                  className="px-2 py-1 text-[11px] border border-navy-200 rounded-sm text-navy-600 hover:bg-navy-50 text-left">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {lich.map((l, i) => (
          <div key={i} className="space-y-2">
            <div className="flex justify-end">
              <p className="max-w-[85%] bg-navy-700 text-white text-xs px-3 py-2 rounded-sm">{l.hoi}</p>
            </div>

            {l.loi || !l.dap ? (
              <p className="text-xs text-crimson-700 bg-crimson-50 border border-crimson-200 px-3 py-2 rounded-sm">
                Không hỏi được. Kiểm tra kết nối tới máy chủ rồi thử lại.
              </p>
            ) : (
              <div className="space-y-2">
                <div className="text-xs text-navy-800 leading-relaxed
                                [&_p]:mb-1.5 [&_p:last-child]:mb-0
                                [&_ul]:list-disc [&_ul]:pl-4 [&_ul]:space-y-0.5
                                [&_ol]:list-decimal [&_ol]:pl-4
                                [&_strong]:font-semibold [&_strong]:text-navy-900">
                  <ReactMarkdown>{l.dap.tra_loi}</ReactMarkdown>
                </div>

                {/* Nguồn số liệu — để người đọc biết câu trả lời dựa vào đâu */}
                {l.dap.cong_cu_da_dung.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1">
                    <Database size={10} className="text-navy-400" />
                    {[...new Set(l.dap.cong_cu_da_dung)].map(c => (
                      <span key={c} className="text-[9px] px-1.5 py-0.5 bg-navy-50 border border-navy-200 rounded-sm text-navy-600">
                        {NHAN_CONG_CU[c] ?? c}
                      </span>
                    ))}
                  </div>
                )}

                {l.dap.dieu_khoan?.map(c => (
                  <div key={c.id} className="border border-navy-100 rounded-sm">
                    <div className="px-2.5 py-1.5 bg-navy-50/60 border-b border-navy-100 flex items-start gap-1.5">
                      <FileText size={11} className="text-navy-400 shrink-0 mt-0.5" />
                      <p className="text-[11px] font-medium text-navy-800 leading-snug">{c.title}</p>
                    </div>
                    <p className="px-2.5 py-2 text-[11px] text-navy-700 whitespace-pre-line leading-relaxed">
                      {c.text}
                    </p>
                    <p className="px-2.5 pb-1.5 text-[10px] text-navy-400">{c.source}</p>
                  </div>
                ))}

                {l.dap.che_do === 'tai_cho' && (
                  <p className="text-[10px] text-gold-700 bg-gold-50 border border-gold-200 px-2 py-1 rounded-sm">
                    Đang trả lời bằng máy tra cứu tại chỗ{l.dap.ghi_chu ? ` — ${l.dap.ghi_chu}` : ''}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}

        {dangHoi && <p className="text-[11px] text-navy-400">Đang tra cứu…</p>}

        {lich.length === 0 && (
          <div className="border-t border-navy-100 pt-2">
            <button onClick={xemDanhMuc}
              className="text-[11px] text-navy-600 hover:text-navy-800 flex items-center gap-1">
              {moDanhMuc ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              Xem toàn bộ điều khoản đã lập chỉ mục{dieuKhoan ? ` (${dieuKhoan.length})` : ''}
            </button>
            {moDanhMuc && (
              <div className="mt-2 space-y-1">
                {dieuKhoan === null && <p className="text-[11px] text-navy-400">Đang tải…</p>}
                {dieuKhoan?.map(c => (
                  <div key={c.id} className="border border-navy-100 rounded-sm">
                    <button onClick={() => setDangXem(dangXem === c.id ? null : c.id)}
                      className="w-full text-left px-2.5 py-1.5 flex items-start gap-1.5 hover:bg-navy-50/60">
                      <FileText size={11} className="text-navy-400 shrink-0 mt-0.5" />
                      <span className="text-[11px] text-navy-800 leading-snug">{c.title}</span>
                    </button>
                    {dangXem === c.id && (
                      <p className="px-2.5 pb-2 pt-1.5 text-[11px] text-navy-700 whitespace-pre-line
                                    leading-relaxed border-t border-navy-100">{c.text}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div ref={cuoiRef} />
      </div>

      <form onSubmit={e => { e.preventDefault(); hoi(q); }}
        className="shrink-0 border-t border-navy-200 p-2 flex gap-2">
        <input ref={oNhapRef} value={q} onChange={e => setQ(e.target.value)}
          placeholder="Hỏi về nhiệm vụ, điểm KPI, cách tính điểm…"
          className="flex-1 px-2.5 py-1.5 border border-navy-200 rounded-sm text-xs" />
        <button type="submit" disabled={dangHoi || !q.trim()}
          className="px-2.5 bg-navy-700 text-white rounded-sm hover:bg-navy-800 disabled:opacity-40 shrink-0">
          <Send size={14} />
        </button>
      </form>

      <p className="shrink-0 px-3 pb-2 text-[9px] text-navy-400 leading-tight">
        Trợ lý chỉ đọc dữ liệu trong phạm vi đồng chí có quyền xem. Nhiệm vụ có độ mật
        chỉ được thống kê số lượng, không nêu tên. Trợ lý không giao việc và không chấm điểm.
      </p>
    </div>
  );
};
