/**
 * Ghép danh sách class, bỏ qua giá trị rỗng/false/undefined.
 *
 * Cố tình KHÔNG dùng `clsx` + `tailwind-merge`: dự án không có hai gói đó và
 * các component ở đây đặt class biến thể trước, class truyền từ ngoài sau, nên
 * quy tắc "khai báo sau thắng" của CSS đã đủ để ghi đè.
 */
export function cn(...parts) {
  return parts.filter(Boolean).join(' ');
}

export default cn;
