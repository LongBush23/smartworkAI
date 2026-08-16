import { useState, useRef, useEffect } from 'react';
import {
  MessageCircleQuestion, X, Send, FileText, ChevronDown, ChevronRight, BookOpen,
} from 'lucide-react';
import { aiApi } from '../lib/ai-api';
import type { GuidelineAnswer, GuidelineClause } from '../lib/ai-api';

/**
 * Hộp tra cứu Hướng dẫn 20-HD/ĐUCA, mở được ở mọi trang.
 *
 * Trả lời TẠI CHỖ bằng máy quy tắc + tìm điều khoản của backend, không gọi
 * dịch vụ ngoài. Câu trả lời về con số lấy trực tiếp từ hằng số của bộ máy
 * chấm điểm nên luôn khớp với điều hệ thống thực sự tính.
 *
 * Cố ý KHÔNG dựng thành trợ lý hội thoại tổng quát: đây là văn bản pháp quy,
 * cán bộ cần nguyên văn điều khoản để trích dẫn chứ không cần bản diễn giải
 * có thể sai lệch.
 */

const GOI_Y = [
  'Sửa 3 lần thì tính bao nhiêu phần trăm?',
  'Nhắc nhở 2 lần được bao nhiêu điểm?',
  'KPI 65 thuộc nhóm mấy?',
  'Công thức tính KPI cho lãnh đạo, chỉ huy',
  'Tiêu chí chung tối đa bao nhiêu điểm?',
  'Quy trình đánh giá gồm mấy bước?',
];

interface LuotHoi {
  hoi: string;
  dap: GuidelineAnswer | null;
  loi?: boolean;
}

export const HopTraCuu = () => {
  const [mo, setMo] = useState(false);
  const [q, setQ] = useState('');
  const [lich, setLich] = useState<LuotHoi[]>([]);
  const [dangHoi, setDangHoi] = useState(false);

  const [dieuKhoan, setDieuKhoan] = useState<GuidelineClause[] | null>(null);
  const [moDanhMuc, setMoDanhMuc] = useState(false);
  const [dangXem, setDangXem] = useState<string | null>(null);

  const cuoiRef = useRef<HTMLDivElement>(null);
  const oNhapRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (mo) oNhapRef.current?.focus();
  }, [mo]);

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
    try {
      const dap = await aiApi.searchGuideline(c);
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
        title="Tra cứu Hướng dẫn 20-HD/ĐUCA"
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
                 sm:inset-x-auto sm:top-auto sm:right-5 sm:bottom-5 sm:w-[400px] sm:h-[560px]"
    >
      {/* Tiêu đề */}
      <div className="h-12 shrink-0 bg-navy-700 text-white flex items-center px-3 gap-2">
        <BookOpen size={16} className="shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-semibold leading-tight">Tra cứu Hướng dẫn</p>
          <p className="text-[10px] text-navy-200 leading-tight truncate">
            Số 20-HD/ĐUCA · trả lời tại chỗ
          </p>
        </div>
        <button onClick={() => setMo(false)} className="text-navy-200 hover:text-white shrink-0">
          <X size={18} />
        </button>
      </div>

      {/* Hội thoại */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3">
        {lich.length === 0 && (
          <div className="space-y-3">
            <p className="text-xs text-navy-600 leading-relaxed">
              Hỏi về cách tính điểm theo Hướng dẫn. Câu trả lời về con số được lấy trực tiếp
              từ chính bộ máy chấm điểm của hệ thống, kèm trích dẫn nguyên văn điều khoản.
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
            {/* Câu hỏi */}
            <div className="flex justify-end">
              <p className="max-w-[85%] bg-navy-700 text-white text-xs px-3 py-2 rounded-sm">
                {l.hoi}
              </p>
            </div>

            {/* Trả lời */}
            {l.loi || !l.dap ? (
              <p className="text-xs text-crimson-700 bg-crimson-50 border border-crimson-200 px-3 py-2 rounded-sm">
                Không tra cứu được. Kiểm tra kết nối tới máy chủ rồi thử lại.
              </p>
            ) : (
              <div className="space-y-2">
                {l.dap.rule_answer ? (
                  <div className="bg-navy-50 border-l-2 border-navy-600 px-3 py-2">
                    <p className="text-[10px] text-navy-500">{l.dap.rule_answer.question_understood}</p>
                    <p className="text-sm font-bold text-navy-800 mt-0.5">{l.dap.rule_answer.answer}</p>
                    <p className="text-[11px] text-navy-600 mt-1">{l.dap.rule_answer.detail}</p>
                  </div>
                ) : (
                  <p className="text-[11px] text-navy-500 italic">
                    Không nhận diện được câu hỏi về số. Dưới đây là các điều khoản liên quan nhất.
                  </p>
                )}

                {l.dap.clauses.map(c => (
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
              </div>
            )}
          </div>
        ))}

        {dangHoi && <p className="text-[11px] text-navy-400">Đang tra cứu…</p>}

        {/* Danh mục điều khoản */}
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
                                    leading-relaxed border-t border-navy-100">
                        {c.text}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div ref={cuoiRef} />
      </div>

      {/* Ô nhập */}
      <form
        onSubmit={e => { e.preventDefault(); hoi(q); }}
        className="shrink-0 border-t border-navy-200 p-2 flex gap-2"
      >
        <input
          ref={oNhapRef}
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Nhập câu hỏi về cách tính điểm…"
          className="flex-1 px-2.5 py-1.5 border border-navy-200 rounded-sm text-xs"
        />
        <button
          type="submit"
          disabled={dangHoi || !q.trim()}
          className="px-2.5 bg-navy-700 text-white rounded-sm hover:bg-navy-800 disabled:opacity-40 shrink-0"
        >
          <Send size={14} />
        </button>
      </form>

      <p className="shrink-0 px-3 pb-2 text-[9px] text-navy-400 leading-tight">
        Trả lời dựa trên Hướng dẫn số 20-HD/ĐUCA, xử lý tại chỗ trong hệ thống.
        Không gửi dữ liệu ra dịch vụ bên ngoài.
      </p>
    </div>
  );
};
