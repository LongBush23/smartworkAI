import api from './api';

/**
 * Thông tin cán bộ đang đăng nhập, gọi một lần rồi dùng lại.
 *
 * VÌ SAO CẦN
 * ----------
 * Có 9 chỗ trong giao diện gọi `/auth/me`. Mở một trang bất kỳ là thanh điều
 * hướng gọi một lần, bản thân trang gọi thêm lần nữa. Đo trên bản triển khai
 * Render: mỗi lượt mất khoảng 0,5 giây, mà trang chủ lại CHỜ `/auth/me` xong
 * mới gọi các API còn lại — thành chuỗi nối đuôi, tốn hơn một giây chỉ để hỏi
 * đi hỏi lại cùng một câu.
 *
 * Ở máy cục bộ gần như không nhận ra vì độ trễ chỉ vài chục mili giây. Lỗi này
 * chỉ lộ ra khi máy chủ ở xa.
 *
 * Lưu Promise chứ không lưu kết quả: nhiều component cùng gọi trong một nhịp
 * render sẽ dùng chung đúng một yêu cầu mạng thay vì mỗi bên bắn một cái.
 */
let dangCho: Promise<any> | null = null;

export const layMe = (lamMoi = false): Promise<any> => {
  if (lamMoi || !dangCho) {
    dangCho = api.get('/auth/me').then(res => res.data).catch(err => {
      // Hỏng thì bỏ cache, để lần sau còn thử lại được
      dangCho = null;
      throw err;
    });
  }
  return dangCho;
};

/** Gọi khi đăng xuất hoặc đổi tài khoản. */
export const xoaCacheMe = () => { dangCho = null; };
