import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Cpu, Shield, Globe, ScanEye, RefreshCw, ArrowRight, Info, FileCode2,
  CheckCircle2, XCircle,
} from 'lucide-react';
import { aiApi } from '../lib/ai-api';
import type { MoHinh, ChatLuongMoHinh, SoDangKyMoHinh } from '../lib/ai-api';
import { dangXemDauVet, datXemDauVet, useDauVetAI } from '../lib/dau-vet-ai';
import { layMe } from '../lib/me';

/**
 * Trang gom toàn bộ mô hình của hệ thống về một chỗ.
 *
 * Mô tả, thuật toán, lý do chọn thuật toán, tham số và chỉ số chất lượng đều
 * lấy từ sổ đăng ký ở backend (backend/services/so_dang_ky_mo_hinh.py) — trang
 * này không tự viết lại con số nào, để không có hai bản mô tả lệch nhau.
 */

/** Ma trận nhầm lẫn — đọc được mà không cần biết thuật ngữ tp/fp/fn/tn. */
const MaTranNhamLan = ({
  c, nhanDuong,
}: {
  c: { tn: number; fp: number; fn: number; tp: number };
  nhanDuong: string;
}) => (
  <div className="overflow-x-auto">
    <table className="text-[11px] border-collapse">
      <thead>
        <tr>
          <th className="p-1" />
          <th className="p-1 font-medium text-navy-500 text-left">Mô hình báo có</th>
          <th className="p-1 font-medium text-navy-500 text-left">Mô hình báo không</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th className="p-1 font-medium text-navy-500 text-left whitespace-nowrap">
            Thực tế {nhanDuong}
          </th>
          <td className="p-1.5 border border-navy-200 bg-navy-50 tabular">
            <strong className="text-navy-900">{c.tp}</strong>
            <span className="block text-navy-500 text-[10px]">báo đúng</span>
          </td>
          <td className="p-1.5 border border-crimson-200 bg-crimson-50 tabular">
            <strong className="text-crimson-800">{c.fn}</strong>
            <span className="block text-crimson-700 text-[10px]">bỏ sót</span>
          </td>
        </tr>
        <tr>
          <th className="p-1 font-medium text-navy-500 text-left whitespace-nowrap">
            Thực tế không
          </th>
          <td className="p-1.5 border border-gold-200 bg-gold-50 tabular">
            <strong className="text-gold-700">{c.fp}</strong>
            <span className="block text-gold-700 text-[10px]">báo oan</span>
          </td>
          <td className="p-1.5 border border-navy-200 bg-navy-50 tabular">
            <strong className="text-navy-900">{c.tn}</strong>
            <span className="block text-navy-500 text-[10px]">báo đúng</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
);

/** Khối định lượng của một mô hình hồi quy. */
const KhoiChatLuong = ({
  cl, nguong, nhanDuong,
}: {
  cl: ChatLuongMoHinh;
  nguong: number;
  nhanDuong: string;
}) => {
  const auc = cl.auc ?? 0;
  const dat = cl.usable === true;
  // Chuẩn hoá thanh hệ số theo hệ số lớn nhất, để so được độ nặng giữa các đặc trưng
  const heSoLonNhat = Math.max(...cl.dac_trung.map(d => Math.abs(d.he_so)), 0.001);

  if (cl.usable === false && cl.auc == null) {
    return (
      <div className="bg-gold-50 border border-gold-200 rounded-sm px-3 py-2">
        <p className="text-[11px] text-gold-700">{cl.reason}</p>
      </div>
    );
  }

  return (
    <div className="border border-navy-200 rounded-sm">
      <p className="section-label px-3 py-1.5 bg-navy-50 border-b border-navy-200">
        Chất lượng đo trên tập kiểm tra tách riêng
      </p>

      <div className="p-3 space-y-3">
        {/* AUC so với ngưỡng */}
        <div>
          <div className="flex items-baseline justify-between gap-2">
            <p className="text-xs text-navy-600">
              AUC <span className="text-navy-400">(ngưỡng tối thiểu {nguong.toFixed(2)})</span>
            </p>
            <p className="flex items-center gap-1.5">
              <span className={`text-lg font-bold tabular ${dat ? 'text-navy-800' : 'text-crimson-700'}`}>
                {auc.toFixed(3)}
              </span>
              {dat ? (
                <span className="flex items-center gap-1 text-[10px] text-navy-600 bg-navy-100 border border-navy-200 px-1.5 py-px rounded-sm">
                  <CheckCircle2 size={10} /> đạt ngưỡng, đang được dùng
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[10px] text-crimson-800 bg-crimson-50 border border-crimson-200 px-1.5 py-px rounded-sm">
                  <XCircle size={10} /> chưa đạt, không đưa ra dùng
                </span>
              )}
            </p>
          </div>
          {/* Vạch ngưỡng vẽ ngay trên thanh: nhìn là biết vượt hay chưa */}
          <div className="relative mt-1.5 h-2 bg-navy-100 rounded-sm overflow-hidden">
            <div
              className={`h-full ${dat ? 'bg-navy-600' : 'bg-crimson-500'}`}
              style={{ width: `${Math.min(auc, 1) * 100}%` }}
            />
          </div>
          <div className="relative h-3">
            <span
              className="absolute top-0 -translate-x-1/2 text-[9px] text-navy-400 whitespace-nowrap"
              style={{ left: `${nguong * 100}%` }}
            >
              ▲ {nguong.toFixed(2)}
            </span>
          </div>
          {cl.reason && (
            <p className="text-[11px] text-crimson-700 mt-1">{cl.reason}</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="bg-navy-50 rounded-sm px-2.5 py-1.5">
            <p className="text-[10px] text-navy-500">Số mẫu huấn luyện</p>
            <p className="text-sm font-bold text-navy-800 tabular">{cl.n_samples ?? '—'}</p>
          </div>
          <div className="bg-navy-50 rounded-sm px-2.5 py-1.5">
            <p className="text-[10px] text-navy-500">Trong đó trường hợp dương</p>
            <p className="text-sm font-bold text-navy-800 tabular">{cl.n_positive ?? '—'}</p>
          </div>
        </div>

        {cl.confusion && <MaTranNhamLan c={cl.confusion} nhanDuong={nhanDuong} />}

        {/* Bảng hệ số — đây là chỗ thấy rõ mô hình giải thích được, không phải hộp đen */}
        {cl.dac_trung.length > 0 && (
          <div>
            <p className="text-xs font-medium text-navy-700 mb-1">
              Hệ số từng đặc trưng
              <span className="font-normal text-navy-400"> · sắp theo mức ảnh hưởng</span>
            </p>
            <div className="space-y-1">
              {cl.dac_trung.map(d => {
                const duong = d.he_so >= 0;
                const rong = (Math.abs(d.he_so) / heSoLonNhat) * 50;
                // Hệ số làm tròn về 0 nghĩa là đặc trưng không tác động. Vẫn viết
                // "→ tăng nguy cơ" cho nó thì người đọc hiểu ngược hẳn ý nghĩa.
                const khongTacDong = Math.abs(d.he_so) < 0.0005;
                return (
                  <div key={d.ten} className="grid grid-cols-[minmax(0,1fr)_7rem_3rem] items-center gap-2">
                    <div className="min-w-0">
                      <p className="text-[11px] font-mono text-navy-700 truncate">{d.ten}</p>
                      <p className="text-[10px] text-navy-500 truncate">
                        {khongTacDong
                          ? 'không tác động tới kết quả'
                          : `${duong ? d.khi_cao : d.khi_thap} → tăng nguy cơ`}
                      </p>
                    </div>
                    {/* Thanh hai chiều: gốc ở giữa, sang phải là làm tăng nguy cơ */}
                    <div className="relative h-2 bg-navy-50 rounded-sm">
                      <div className="absolute inset-y-0 left-1/2 w-px bg-navy-300" />
                      <div
                        className={`absolute inset-y-0 ${duong ? 'bg-crimson-500' : 'bg-navy-500'}`}
                        style={
                          duong
                            ? { left: '50%', width: `${rong}%` }
                            : { right: '50%', width: `${rong}%` }
                        }
                      />
                    </div>
                    <p className={`text-[11px] tabular text-right ${duong ? 'text-crimson-700' : 'text-navy-600'}`}>
                      {d.he_so > 0 ? '+' : ''}{d.he_so.toFixed(3)}
                    </p>
                  </div>
                );
              })}
            </div>
            <p className="text-[10px] text-navy-400 mt-1.5 leading-relaxed">
              Hệ số dương: giá trị đặc trưng càng cao thì nguy cơ càng tăng. Hệ số âm thì
              ngược lại. Đóng góp của một đặc trưng vào kết quả là hệ số × giá trị đã
              chuẩn hoá — chính con số đó sinh ra dòng lý do kèm mỗi cảnh báo.
            </p>
          </div>
        )}

        {cl.trained_at && (
          <p className="text-[10px] text-navy-400">
            Huấn luyện lúc {new Date(cl.trained_at + 'Z').toLocaleString('vi-VN')}
          </p>
        )}
      </div>
    </div>
  );
};

const TheMoHinh = ({ m, nguong }: { m: MoHinh; nguong: number }) => {
  const goiRaNgoai = m.noi_chay === 'goi_ra_ngoai';

  return (
    <div id={m.ma} className="bg-white border border-navy-200 rounded-sm scroll-mt-4">
      <div className="px-4 py-2.5 border-b border-navy-200 bg-navy-50 flex items-start gap-2.5">
        <span className="shrink-0 h-6 w-6 rounded-sm bg-navy-700 text-white text-xs font-bold flex items-center justify-center tabular">
          {m.so}
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-bold text-navy-900 leading-tight">{m.ten}</h2>
          <p className="text-[11px] text-navy-500 mt-0.5">{m.thuat_toan}</p>
        </div>
        <span
          className={`shrink-0 flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-sm border ${
            goiRaNgoai
              ? 'bg-gold-50 border-gold-300 text-gold-700'
              : 'bg-navy-100 border-navy-300 text-navy-700'
          }`}
        >
          {goiRaNgoai ? <Globe size={10} /> : <Shield size={10} />}
          {goiRaNgoai ? 'Gọi ra ngoài' : 'Chạy tại chỗ'}
        </span>
      </div>

      <div className="p-4 space-y-3">
        <div>
          <p className="section-label mb-0.5">Mục đích</p>
          <p className="text-xs text-navy-700 leading-relaxed">{m.muc_dich}</p>
        </div>

        <div>
          <p className="section-label mb-0.5">Vì sao chọn thuật toán này</p>
          <p className="text-xs text-navy-700 leading-relaxed">{m.vi_sao}</p>
        </div>

        <div>
          <p className="section-label mb-1">Tham số đang dùng</p>
          <dl className="divide-y divide-navy-100 border border-navy-100 rounded-sm">
            {m.tham_so.map(t => (
              <div key={t.nhan} className="flex items-baseline justify-between gap-3 px-2.5 py-1">
                <dt className="text-[11px] text-navy-600">{t.nhan}</dt>
                <dd className="text-[11px] font-medium text-navy-800 tabular text-right">{t.gia_tri}</dd>
              </div>
            ))}
          </dl>
        </div>

        {m.chat_luong && (
          <KhoiChatLuong
            cl={m.chat_luong}
            nguong={nguong}
            nhanDuong={m.ma === 'nguy_co_tre_han' ? 'trễ hạn' : 'rơi Nhóm 3'}
          />
        )}

        <div>
          <p className="section-label mb-1">Đang được dùng ở</p>
          <div className="flex flex-wrap gap-1.5">
            {m.dung_o.map(d => (
              <Link
                key={d.nhan}
                to={d.duong_dan}
                className="flex items-center gap-1 text-[11px] text-navy-700 border border-navy-300
                           rounded-sm px-2 py-1 hover:bg-navy-50"
              >
                {d.nhan} <ArrowRight size={11} className="shrink-0" />
              </Link>
            ))}
          </div>
        </div>

        <p className="text-[10px] text-navy-400 flex items-center gap-1 font-mono">
          <FileCode2 size={11} className="shrink-0" /> {m.ma_nguon}
        </p>
      </div>
    </div>
  );
};

const MoHinhAI = () => {
  const { hash } = useLocation();
  const xemDauVet = useDauVetAI();
  const [so, setSo] = useState<SoDangKyMoHinh | null>(null);
  const [loi, setLoi] = useState(false);
  const [dangTai, setDangTai] = useState(true);
  const [dangHuanLuyen, setDangHuanLuyen] = useState(false);
  const [laQuanTri, setLaQuanTri] = useState(false);

  useEffect(() => { tai(); }, []);

  // Nhảy tới đúng thẻ mô hình khi vào từ nhãn dấu vết AI. Phải đợi dữ liệu về
  // mới cuộn được: lúc còn đang tải thì phần tử chưa có trong trang.
  //
  // Cuộn tức thì, KHÔNG dùng behavior 'smooth': trang này dài hơn 3000px nên
  // hiệu ứng bay qua bốn thẻ vừa lâu vừa mất phương hướng, và có môi trường bỏ
  // qua hẳn hiệu ứng đó khiến trang đứng nguyên ở đầu — đo được trên chính bản
  // chạy thử này.
  useEffect(() => {
    if (!so || !hash) return;
    document.getElementById(hash.slice(1))?.scrollIntoView({ block: 'start' });
  }, [so, hash]);

  const tai = async () => {
    setDangTai(true);
    setLoi(false);
    try {
      const [me, kq] = await Promise.all([layMe().catch(() => null), aiApi.moHinh()]);
      setLaQuanTri(me?.role === 'admin');
      setSo(kq);
    } catch {
      setLoi(true);
    } finally {
      setDangTai(false);
    }
  };

  const huanLuyenLai = async () => {
    try {
      setDangHuanLuyen(true);
      const r = await aiApi.retrain();
      toast.success(
        `Đã huấn luyện lại · Trễ hạn AUC ${r.task_late?.auc ?? '—'} · Nhóm 3 AUC ${r.group3?.auc ?? '—'}`,
        { duration: 5000 },
      );
      await tai();
    } catch {
      toast.error('Không huấn luyện lại được');
    } finally {
      setDangHuanLuyen(false);
    }
  };

  if (dangTai) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-600" />
      </div>
    );
  }

  if (loi || !so) {
    return (
      <div className="bg-white border border-navy-200 rounded-sm p-8 text-center">
        <p className="text-sm text-crimson-700 font-medium">Không tải được sổ đăng ký mô hình</p>
        <button onClick={tai} className="mt-3 px-3 py-1.5 border border-navy-300 rounded-sm text-xs text-navy-700 hover:bg-navy-50">
          Thử lại
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 justify-between items-start">
        <div>
          <h1 className="text-xl font-bold text-navy-900 flex items-center gap-2">
            <Cpu className="h-5 w-5 text-navy-700" /> Mô hình hỗ trợ ra quyết định
          </h1>
          <p className="text-xs text-navy-500 mt-0.5">
            {so.mo_hinh.length} mô hình đang chạy trong hệ thống — mục đích, thuật toán,
            tham số và chất lượng đo được.
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => datXemDauVet(!dangXemDauVet())}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-sm text-xs border ${
              xemDauVet
                ? 'bg-teal-700 border-teal-700 text-white hover:bg-teal-800'
                : 'border-navy-300 text-navy-700 hover:bg-navy-50'
            }`}
          >
            <ScanEye size={13} />
            {xemDauVet ? 'Đang xem dấu vết AI' : 'Xem dấu vết AI'}
          </button>
          {laQuanTri && (
            <button
              onClick={huanLuyenLai}
              disabled={dangHuanLuyen}
              className="flex items-center gap-1.5 px-2.5 py-1.5 border border-navy-300 rounded-sm
                         text-xs text-navy-700 hover:bg-navy-50 disabled:opacity-50"
            >
              <RefreshCw size={13} className={dangHuanLuyen ? 'animate-spin' : ''} />
              {dangHuanLuyen ? 'Đang huấn luyện…' : 'Huấn luyện lại mô hình dự báo'}
            </button>
          )}
        </div>
      </div>

      {/* Hai ranh giới cứng — đặt trước mọi con số vì đây là điều cần biết trước */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {so.ranh_gioi.map((r, i) => (
          <div key={r.tieu_de} className="bg-navy-900 text-white rounded-sm p-4">
            <p className="text-[13px] font-semibold flex items-start gap-2 leading-snug">
              <span className="shrink-0 h-5 w-5 rounded-sm bg-gold-400 text-navy-900 text-[11px] font-bold flex items-center justify-center tabular">
                {i + 1}
              </span>
              {r.tieu_de}
            </p>
            <p className="text-[11px] text-navy-200 leading-relaxed mt-1.5">{r.noi_dung}</p>
          </div>
        ))}
      </div>

      <div className="bg-gold-50 border border-gold-300 rounded-sm px-3 py-2 flex items-start gap-2">
        <Info size={13} className="text-gold-700 shrink-0 mt-0.5" />
        <div>
          <p className="text-[11px] font-semibold text-gold-700">
            Đọc chỉ số AUC dưới đây cho đúng
          </p>
          <p className="text-[11px] text-navy-700 leading-relaxed mt-0.5">
            {so.ghi_chu_du_lieu_mau}
          </p>
        </div>
      </div>

      <p className="text-[11px] text-navy-500 flex items-start gap-1.5">
        <ScanEye size={12} className="shrink-0 mt-0.5 text-teal-700" />
        Bật <strong className="font-medium text-navy-700">Xem dấu vết AI</strong> rồi đi lại các
        trang: mọi khối do mô hình sinh ra sẽ được viền lại và gắn số hiệu, bấm nhãn là quay
        về đúng thẻ mô hình ở trang này.
      </p>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        {so.mo_hinh.map(m => (
          <TheMoHinh key={m.ma} m={m} nguong={so.auc_threshold} />
        ))}
      </div>
    </div>
  );
};

export default MoHinhAI;
