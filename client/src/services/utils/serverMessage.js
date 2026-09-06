/**
 * Đổi phần thân lỗi/thành công của backend thành câu hiển thị.
 *
 * Backend trả `{ message, code, params }` — xem `server_python/app/messages.py`.
 * Thứ tự ưu tiên dưới đây được dùng ở **mọi** chỗ hiện thông báo của server;
 * gom về một hàm để ba trang gợi ý việc làm và `useMutationToast` không thể
 * lệch nhau (trước đó bốn chỗ chép tay cùng một đoạn sáu dòng):
 *
 *   1. bản dịch của `code`  — đúng ngôn ngữ người dùng đang xem
 *   2. `message` của server — tiếng Việt, dùng khi mã chưa có bản dịch
 *   3. câu dự phòng         — khi request chết trước đó (mất mạng, CORS) nên
 *                             không có body nào để đọc
 *
 * Bỏ bước 2 thì một mã chưa dịch sẽ hiện ra khoá thô `server.post.xyz`; bỏ
 * bước 3 thì mất mạng là toast rỗng.
 *
 * @param t            hàm dịch của component (phải có namespace `error`)
 * @param payload      `response.data` hoặc `error.data`
 * @param fallbackKey  khoá của câu dự phòng, mặc định là câu chung
 */
export const serverMessage = (t, payload, fallbackKey = 'error:ui.networkFallback') => {
  const code = payload?.code;
  if (code) {
    const translated = t(`error:server.${code}`, {
      ...(payload?.params || {}),
      defaultValue: '',
    });
    if (translated) return translated;
  }
  return payload?.message || t(fallbackKey);
};
