import { isRejectedWithValue } from '@reduxjs/toolkit';
import { logger } from '../../logger';

/**
 * Ghi lại MỌI request API thất bại, ở một chỗ duy nhất.
 *
 * Trước đây mỗi component tự đọc `error?.data?.message` để hiện toast (27 chỗ),
 * nên lỗi nào không có toast thì biến mất không dấu vết. Middleware này đứng ở
 * tầng RTK Query nên thấy được tất cả, kể cả các query chạy nền.
 *
 * 401 KHÔNG được coi là lỗi: `baseQueryWithReauth` gặp 401 sẽ tự gia hạn token
 * rồi thử lại, đó là luồng bình thường. Ghi lại chỉ tạo nhiễu.
 */
export const rtkQueryErrorLogger = () => (next) => (action) => {
  if (isRejectedWithValue(action)) {
    const status = action.payload?.status;
    if (status !== 401) {
      logger.warn('api.error', {
        message: `${action.meta?.arg?.endpointName || 'unknown'} → ${status}: ${
          action.payload?.data?.message || action.error?.message || 'không rõ'
        }`,
      });
    }
  }
  return next(action);
};

export default rtkQueryErrorLogger;
