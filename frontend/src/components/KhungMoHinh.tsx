import { Link } from 'react-router-dom';
import { ScanEye, Globe } from 'lucide-react';
import { MO_HINH_DA_GAN, useDauVetAI } from '../lib/dau-vet-ai';

/**
 * Viền và gắn nhãn cho một khối do mô hình sinh ra, khi bật chế độ xem dấu vết.
 *
 * Tắt chế độ thì KHÔNG bọc thêm thẻ nào — trả về đúng children. Bọc thêm một
 * div cả ngày chỉ để lúc nào cần mới dùng sẽ đổi bố cục ở những chỗ cha là
 * flex hoặc grid.
 *
 * Dùng `outline` chứ không dùng `ring`: ring cần biết màu nền phía sau để vẽ
 * khoảng đệm, mà khối mô hình nằm cả trên nền xám của trang lẫn trên thẻ trắng.
 */
export const KhungMoHinh = ({
  ma,
  children,
}: {
  ma: keyof typeof MO_HINH_DA_GAN | string;
  children: React.ReactNode;
}) => {
  const bat = useDauVetAI();
  if (!bat) return <>{children}</>;

  const m = MO_HINH_DA_GAN[ma];
  if (!m) return <>{children}</>;

  const goiRaNgoai = ma === 'tro_ly_hoi_thoai';

  return (
    <div className="relative outline outline-2 outline-teal-600 outline-offset-2 rounded-sm">
      <Link
        to={`/kpi/models#${ma}`}
        title="Xem mô hình này ở trang Mô hình hỗ trợ ra quyết định"
        className="absolute -top-2.5 left-2 z-20 flex items-center gap-1 px-1.5 py-px
                   bg-teal-700 text-white text-[10px] font-medium rounded-sm
                   shadow-sm hover:bg-teal-800 max-w-[calc(100%-1rem)]"
      >
        {goiRaNgoai ? <Globe size={10} className="shrink-0" /> : <ScanEye size={10} className="shrink-0" />}
        <span className="truncate">
          Mô hình {m.so} · {m.ten} · {goiRaNgoai ? 'gọi ra ngoài' : 'chạy tại chỗ'}
        </span>
      </Link>
      {children}
    </div>
  );
};
