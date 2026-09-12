import { useTranslation } from 'react-i18next';
import { FaFileCirclePlus } from 'react-icons/fa6';
import Page from '../../../Page';
import EmptyState from '../../../../components/ui/EmptyState';
import LinkButton from '../../../../components/ui/LinkButton';
import { serverMessage } from '../../../../services/utils/serverMessage';

/**
 * Màn hình lỗi dùng chung cho bốn trang Match.
 *
 * Cả bốn trang đều lặp lại cùng một khối lỗi chép tay. Gom về một chỗ để nút
 * thoát ra luôn giống nhau và không trang nào bị bỏ quên khi sửa.
 *
 * Hiện CÂU LỖI THẬT từ máy chủ chứ không viết cứng "bạn cần tạo CV": mất mạng
 * hay lỗi 500 cũng rơi vào đây, mà nói "bạn cần tạo CV" khi người ta đã có CV
 * thì họ đi tìm sai chỗ.
 */
function MatchError({
  error,
  fallbackKey = 'loadFailed',
  to = '/resume',
  actionKey = 'createResume',
}) {
  const { t } = useTranslation(['match', 'error']);
  return (
    <Page rail={false}>
      <EmptyState
        icon={FaFileCirclePlus}
        title={serverMessage(t, error?.data, fallbackKey)}
        action={
          <LinkButton to={to} variant='accent'>
            {t(actionKey)}
          </LinkButton>
        }
      />
    </Page>
  );
}

export default MatchError;
