import { useState } from 'react';
import { BookOpen, Search, FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { aiApi } from '../lib/ai-api';
import type { GuidelineAnswer } from '../lib/ai-api';

const GOI_Y = [
  'Sửa 3 lần thì tính bao nhiêu phần trăm?',
  'Nhắc nhở 2 lần được bao nhiêu điểm?',
  'KPI 65 thuộc nhóm mấy?',
  'Công thức tính KPI cho lãnh đạo',
  'Tiêu chí chung tối đa bao nhiêu điểm?',
];

/** Ô tra cứu Hướng dẫn 20-HD/ĐUCA — chạy tại chỗ, không gọi dịch vụ ngoài. */
export const GuidelineLookup = ({ collapsed = true }: { collapsed?: boolean }) => {
  const [open, setOpen] = useState(!collapsed);
  const [q, setQ] = useState('');
  const [result, setResult] = useState<GuidelineAnswer | null>(null);
  const [loading, setLoading] = useState(false);

  const ask = async (question: string) => {
    if (!question.trim()) return;
    setQ(question);
    setLoading(true);
    try {
      setResult(await aiApi.searchGuideline(question));
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-navy-200 rounded-sm">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-left hover:bg-navy-50/50"
      >
        <span className="section-label flex items-center gap-1.5">
          <BookOpen size={13} /> Tra cứu Hướng dẫn 20-HD/ĐUCA
        </span>
        {open ? <ChevronDown size={15} className="text-navy-400" /> : <ChevronRight size={15} className="text-navy-400" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3">
          <form onSubmit={e => { e.preventDefault(); ask(q); }} className="flex gap-2">
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              placeholder="VD: sửa 3 lần thì tính bao nhiêu phần trăm?"
              className="flex-1 px-3 py-2 border border-navy-200 rounded-sm text-sm"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-3 py-2 bg-navy-700 text-white rounded-sm hover:bg-navy-800 disabled:opacity-50 shrink-0"
            >
              <Search size={16} />
            </button>
          </form>

          {!result && (
            <div className="flex flex-wrap gap-1.5">
              {GOI_Y.map(s => (
                <button
                  key={s}
                  onClick={() => ask(s)}
                  className="px-2 py-1 text-[11px] border border-navy-200 rounded-sm text-navy-600 hover:bg-navy-50"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {loading && <p className="text-xs text-navy-400">Đang tra cứu…</p>}

          {result && (
            <div className="space-y-3">
              {result.rule_answer && (
                <div className="bg-navy-50 border-l-2 border-navy-600 px-3 py-2.5">
                  <p className="text-[11px] text-navy-500">{result.rule_answer.question_understood}</p>
                  <p className="text-base font-bold text-navy-800 mt-0.5">{result.rule_answer.answer}</p>
                  <p className="text-xs text-navy-600 mt-1">{result.rule_answer.detail}</p>
                </div>
              )}

              {result.clauses.map(c => (
                <div key={c.id} className="border border-navy-100 rounded-sm">
                  <div className="px-3 py-1.5 bg-navy-50/60 border-b border-navy-100 flex items-center gap-1.5">
                    <FileText size={12} className="text-navy-400 shrink-0" />
                    <p className="text-xs font-medium text-navy-800">{c.title}</p>
                    <span className="ml-auto text-[10px] text-navy-400 shrink-0">{c.source}</span>
                  </div>
                  <p className="px-3 py-2 text-xs text-navy-700 whitespace-pre-line leading-relaxed">
                    {c.text}
                  </p>
                </div>
              ))}

              <p className="text-[10px] text-navy-400 leading-relaxed">
                {result.explanation} {result.precision_note}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
