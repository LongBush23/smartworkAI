import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Cpu, ShieldAlert, FileText, Bot, ArrowRight } from 'lucide-react';
import { aiApi } from '../lib/ai-api';
import type { TheHoTroAI } from '../lib/ai-api';

/**
 * Dải "AI đang hỗ trợ đồng chí" trên Trang chủ.
 *
 * VÌ SAO CÓ DẢI NÀY
 * -----------------
 * Các mô hình chỉ hiện ra khi có việc cần cảnh báo. Kỳ nào yên ổn thì cả trang
 * không còn dấu vết nào cho thấy hệ thống có mô hình — người dùng kết luận là
 * "chẳng có gì" chứ không phải "không có gì bất thường". Dải này luôn hiện, nêu
 * đúng những thứ phần còn lại của Trang chủ CHƯA nói: có bao nhiêu mô hình, bao
 * nhiêu chạy tại chỗ, tra cứu được bao nhiêu điều khoản, trợ lý đang ở chế độ nào.
 *
 * Số thẻ do máy chủ quyết định theo chức vụ người xem — giao diện chỉ vẽ những
 * gì nhận được, không tự lọc, để phạm vi hiển thị và phạm vi dữ liệu là một.
 */

const BIEU_TUONG: Record<string, typeof Cpu> = {
  mo_hinh: Cpu,
  ra_soat: ShieldAlert,
  dieu_khoan: FileText,
  tro_ly: Bot,
};

const NoiDungThe = ({ t }: { t: TheHoTroAI }) => {
  const Icon = BIEU_TUONG[t.ma] ?? Cpu;
  return (
    <>
      <div className="flex items-start justify-between gap-2">
        <p className="text-[11px] text-navy-500 leading-tight">{t.nhan}</p>
        <Icon size={15} className="text-navy-400 shrink-0" />
      </div>
      <p className="text-xl font-bold text-navy-800 mt-1 leading-tight">{t.so}</p>
      <p className="text-[10px] text-navy-400 mt-0.5 leading-snug">{t.phu}</p>
    </>
  );
};

export const DaiHoTroAI = () => {
  const [the, setThe] = useState<TheHoTroAI[] | null>(null);

  useEffect(() => {
    aiApi.tomTat().then(setThe).catch(() => setThe([]));
  }, []);

  // Không có thẻ nào thì im lặng biến mất, không để lại khung rỗng
  if (the !== null && the.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-5 py-2 border-b border-gray-100 flex items-center gap-2">
        <Cpu size={14} className="text-navy-600 shrink-0" />
        <p className="text-xs font-semibold text-navy-700">Mô hình đang hỗ trợ đồng chí</p>
        <span className="text-[10px] text-navy-400 hidden sm:inline">
          · gợi ý và cảnh báo, không quyết định điểm KPI
        </span>
      </div>

      {/*
        Số cột bám theo số thẻ thực nhận. Để cứng 4 cột thì cán bộ không giữ chức
        vụ — chỉ có 3 thẻ — thấy dải hụt mất một phần tư bên phải, trông như hỏng.
        Lớp Tailwind phải viết đủ chữ, không ghép chuỗi, nếu không trình biên dịch
        không thấy để sinh CSS.
      */}
      <div
        className={`grid grid-cols-2 divide-x divide-y lg:divide-y-0 divide-gray-100 ${
          (the?.length ?? 4) >= 4 ? 'lg:grid-cols-4' : 'lg:grid-cols-3'
        }`}
      >
        {the === null
          ? [0, 1, 2, 3].map(i => (
              <div key={i} className="p-4">
                <p className="text-[11px] text-navy-300">Đang đếm…</p>
                <p className="text-xl font-bold text-navy-200 mt-1">–</p>
              </div>
            ))
          : the.map(t =>
              t.duong_dan ? (
                <Link
                  key={t.ma}
                  to={t.duong_dan}
                  className="p-4 hover:bg-navy-50/60 transition-colors group"
                >
                  <NoiDungThe t={t} />
                  <span className="text-[10px] text-navy-600 mt-1 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    Xem chi tiết <ArrowRight size={10} />
                  </span>
                </Link>
              ) : (
                <div key={t.ma} className="p-4">
                  <NoiDungThe t={t} />
                </div>
              ),
            )}
      </div>
    </div>
  );
};
