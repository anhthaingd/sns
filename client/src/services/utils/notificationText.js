/**
 * Chữ hiển thị cho một thông báo trong chuông.
 *
 * Cùng khuôn với `serverMessage`: ưu tiên dịch theo `code`, không có bản dịch
 * thì rơi về câu chữ mà backend đã dựng sẵn và lưu kèm trong DB — nên không
 * bao giờ để người dùng nhìn thấy khoá thô.
 *
 * Bản ghi tạo TRƯỚC khi backend có `code` thì không mang mã; chúng đi thẳng
 * vào nhánh dự phòng, nhờ vậy không phải migrate dữ liệu cũ.
 *
 * Mã backend là `notification.postLiked`, khoá dịch là
 * `error:server.notification.postLiked` — cùng một đường dẫn, chỉ khác tiền tố
 * namespace, nên không cần bảng ánh xạ.
 */
export const notificationText = (t, notification) => {
  const code = notification?.code;
  if (code) {
    const translated = t(`error:server.${code}`, {
      ...(notification?.params || {}),
      defaultValue: '',
    });
    if (translated) return translated;
  }
  return notification?.notification || '';
};
