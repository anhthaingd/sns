import { useCallback, useContext, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ModalContext } from '../context/ModalProvider';
import { logger } from '../services/logger';
import { serverMessage } from '../services/utils/serverMessage';

/**
 * Hiện toast cho kết quả của một mutation RTK Query.
 *
 * Thay cho khuôn `useEffect` theo dõi isSuccess/isError vốn bị chép lại 22 nơi.
 * Ngoài chuyện dài dòng, khuôn chép tay còn dễ sai mảng phụ thuộc — ví dụ
 * ChannelListLayout từng theo dõi `isSuccessChannels` (của QUERY danh sách)
 * trong khi cần theo dõi `isSuccessJoin` (của MUTATION tham gia), nên toast
 * hiện sai thời điểm. Gom về một chỗ thì lỗi đó không còn cửa xuất hiện.
 *
 * Dùng:
 *   const [joinChannel, joinResult] = useJoinChannelMutation();
 *   useMutationToast(joinResult);
 *
 * @param result       object kết quả (phần tử thứ hai của hook mutation)
 * @param options.onSuccess  chạy thêm khi thành công (đóng modal, reset form...)
 * @param options.successMessage  ghi đè thông báo thành công
 * @param options.showSuccess  đặt false khi thành công là chuyển trang luôn
 *        (ví dụ đăng nhập) — toast chỉ kịp loé lên rồi biến mất cùng trang cũ
 */
const useMutationToast = (result, options = {}) => {
  const { t } = useTranslation('error');
  const { setVisibleModal } = useContext(ModalContext);
  const { onSuccess, successMessage, showSuccess = true } = options;
  const { data, error, isSuccess, isError } = result || {};

  const resolveMessage = useCallback((payload) => serverMessage(t, payload), [t]);

  useEffect(() => {
    if (!isSuccess) return;
    if (showSuccess) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: successMessage || resolveMessage(data),
        },
      });
    }
    onSuccess?.(data);
    // `onSuccess`/`successMessage` cố ý không nằm trong mảng phụ thuộc: chúng
    // thường là hàm inline, đưa vào sẽ khiến toast hiện lại sau mỗi lần render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSuccess, data, setVisibleModal, resolveMessage]);

  useEffect(() => {
    if (!isError) return;
    const message = resolveMessage(error?.data);
    setVisibleModal({
      visibleToastModal: { type: 'error', message },
    });
    // Toast biến mất sau vài giây; log thì còn lại để tra khi có người báo lỗi.
    // Ghi cả `code`: câu chữ đổi theo ngôn ngữ người dùng đang xem, còn mã thì
    // không — tra log theo mã mới gom được mọi lần lỗi giống nhau.
    logger.warn('mutation.failed', { code: error?.data?.code, message });
  }, [isError, error, setVisibleModal, resolveMessage]);
};

export default useMutationToast;
