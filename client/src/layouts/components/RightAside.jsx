import { useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { FaUserGroup } from 'react-icons/fa6';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { ModalContext } from '../../context/ModalProvider';
import Avatar from '../../components/ui/Avatar';

/**
 * Cột phụ bên phải: danh bạ những người mình theo dõi, bấm vào là mở khung chat.
 *
 * Chỉ hiện từ breakpoint xl — dưới đó cột này sẽ bóp phần nội dung chính xuống
 * dưới ngưỡng đọc thoải mái, mà nhắn tin đã có sẵn lối vào ở thanh trên cùng.
 */
function RightAside() {
  const { t } = useTranslation('user');
  const { following } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  const list = following ?? [];

  return (
    <aside className='sticky top-header hidden h-[calc(100vh-theme(spacing.header))] shrink-0 overflow-y-auto overscroll-contain border-l border-line px-3 py-5 xl:block'>
      <h2 className='mb-2 flex items-center gap-2 px-2 text-2xs font-bold uppercase tracking-wider text-fg-subtle'>
        <FaUserGroup className='size-3' aria-hidden='true' />
        {t('profile.following')}
        {list.length > 0 && <span className='tnum ml-auto'>{list.length}</span>}
      </h2>

      {list.length === 0 ? (
        <p className='px-2 py-2 text-xs leading-relaxed text-fg-subtle'>
          {t('following.empty')}
        </p>
      ) : (
        <div className='flex flex-col gap-0.5'>
          {list.map((f) => (
            <button
              key={f?._id}
              type='button'
              className='flex items-center gap-3 rounded-lg p-2 text-left text-sm font-medium text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg'
              onClick={() => setVisibleModal({ visibleChatModal: f })}
              title={t('profile.chat')}
            >
              <Avatar src={f?.avatar} name={f?.username} size='sm' />
              <span className='truncate'>{f?.username}</span>
            </button>
          ))}
        </div>
      )}
    </aside>
  );
}

export default RightAside;
