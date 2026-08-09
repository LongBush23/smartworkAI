import { Lock, EyeOff } from 'lucide-react';
import {
  CLASSIFICATION_COLORS,
  CLASSIFICATION_LABELS,
  type Classification,
} from '../lib/task-api';

/**
 * Tên nhiệm vụ kèm dấu hiệu độ mật.
 *
 * VÌ SAO PHẢI DÙNG CHUNG MỘT CHỖ
 * ------------------------------
 * Trước đây mỗi trang tự vẽ tên nhiệm vụ. Trang chủ vẽ thiếu, nên nhiệm vụ
 * TUYỆT MẬT hiện lên y hệt nhiệm vụ thường: không ổ khoá, không huy hiệu, không
 * cách nào biết đang nhìn tài liệu mật. Máy chủ che dữ liệu đúng, nhưng người
 * xem không được cảnh báo — đó vẫn là lỗi.
 *
 * Mọi nơi hiển thị tên nhiệm vụ PHẢI đi qua component này. Có thêm trang mới
 * thì dùng lại, đừng vẽ tay.
 *
 * Lưu ý: việc che dữ liệu do MÁY CHỦ làm (xem backend/models/security_policy.py).
 * Component này chỉ hiển thị, không phải lớp bảo vệ — người thiếu cấp độ tiếp
 * cận đã nhận `title` là mã hiệu và `is_redacted = true` từ máy chủ.
 */

interface Props {
  title?: string;
  code?: string;
  classification?: Classification;
  isRedacted?: boolean;
  /** Mã hồ sơ gốc — chỉ có khi người xem đủ cấp độ tiếp cận */
  fileReference?: string;
  /** 'day-du' hiện cả huy hiệu; 'gon' chỉ ổ khoá + tên, dùng cho danh sách chật */
  variant?: 'day-du' | 'gon';
  className?: string;
}

const TaskTitle = ({
  title,
  code,
  classification = 'thuong',
  isRedacted = false,
  fileReference,
  variant = 'day-du',
  className = '',
}: Props) => {
  const coDoMat = classification !== 'thuong';

  return (
    <div className={`min-w-0 ${className}`}>
      <div className="flex items-start gap-1.5 min-w-0">
        {coDoMat && (
          <Lock
            size={13}
            className="text-crimson-600 shrink-0 mt-0.5"
            aria-label={`Nhiệm vụ độ ${CLASSIFICATION_LABELS[classification]}`}
          />
        )}
        <p
          className={`truncate font-medium ${
            isRedacted ? 'italic text-navy-400' : 'text-navy-800'
          }`}
          title={title}
        >
          {title || code || '—'}
        </p>
      </div>

      {coDoMat && variant === 'day-du' && (
        <div className="flex flex-wrap items-center gap-1 mt-0.5">
          <span
            className={`px-1.5 py-0 text-[9px] font-bold tracking-wider rounded-sm border ${CLASSIFICATION_COLORS[classification]}`}
          >
            {CLASSIFICATION_LABELS[classification]}
          </span>
          {isRedacted && (
            <span className="inline-flex items-center gap-0.5 text-[9px] text-crimson-600">
              <EyeOff size={9} /> chưa đủ cấp độ tiếp cận
            </span>
          )}
          {fileReference && (
            <span className="text-[9px] text-navy-500 font-mono">{fileReference}</span>
          )}
        </div>
      )}
    </div>
  );
};

export default TaskTitle;
