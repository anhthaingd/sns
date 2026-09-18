import { useCallback, useContext, useEffect, useMemo } from 'react';
import { formatDistanceStrict } from 'date-fns';
import { useTranslation } from 'react-i18next';
import { FaRegComments } from 'react-icons/fa6';
import { currentDateLocale } from '../../i18n/dateLocale';
import { DropdownContext } from '../../context/NotificationProvider';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { ModalContext } from '../../context/ModalProvider';
import { SocketContext } from '../../context/SocketProvider';
import { useReadMessageMutation } from '../../services/redux/query/api/chatApi';
import Popover from '../ui/Popover';
import Avatar from '../ui/Avatar';
import cn from '../../services/utils/cn';

function MessagesDropdown() {
  const { t } = useTranslation('chat');
  const { user, newestMessages, refetchMessages } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  const { state, closeAllDropdown } = useContext(DropdownContext);
  const { isUserOnline } = useContext(SocketContext);
  const [readMessage, { isSuccess: isSuccessReadMessages }] =
    useReadMessageMutation();

  const handleOpenModal = useCallback(
    async (receiver, me, messId) => {
      setVisibleModal({ visibleChatModal: receiver?.user });
      closeAllDropdown();
      if (!me?.isRead) await readMessage(messId);
    },
    [setVisibleModal, closeAllDropdown, readMessage]
  );

  useEffect(() => {
    if (isSuccessReadMessages) refetchMessages();
  }, [isSuccessReadMessages, refetchMessages]);

  const memoMessages = useMemo(
    () =>
      newestMessages.messages?.map((m) => {
        const me =
          m?.sender?.user?._id === user?._id
            ? m?.sender
            : null || m?.receiver?.user?._id === user?._id
              ? m?.receiver
              : null;
        const receiver =
          m?.sender?.user?._id !== user?._id
            ? m?.sender
            : null || m?.receiver?.user?._id !== user?._id
              ? m?.receiver
              : null;
        const unread = !me?.isRead;
        return (
          <li key={m?._id}>
            <button
              type='button'
              className={cn(
                'flex w-full items-center gap-3 rounded-lg p-2.5 text-left transition-colors hover:bg-surface-2',
                unread && 'bg-accent-soft/60'
              )}
              onClick={() => handleOpenModal(receiver, me, m?._id)}
            >
              <Avatar
                src={receiver?.user?.avatar}
                name={receiver?.user?.username}
                size='lg'
                status={isUserOnline(receiver?.user?._id) ? 'online' : undefined}
              />
              <span className='min-w-0 flex-1'>
                <span className='flex items-baseline justify-between gap-2'>
                  <span className='truncate text-sm font-bold text-fg'>
                    {receiver?.user?.username}
                  </span>
                  <span className='tnum shrink-0 text-2xs text-fg-subtle'>
                    {formatDistanceStrict(
                      new Date(Date.now()),
                      new Date(m?.updated_at),
                      { locale: currentDateLocale() }
                    )}
                  </span>
                </span>
                <span
                  className={cn(
                    'mt-0.5 block truncate text-sm',
                    unread ? 'font-semibold text-fg' : 'text-fg-muted'
                  )}
                >
                  {user._id === m?.lastSent && `${t('messages.youPrefix')} `}
                  {m?.content}
                </span>
              </span>
              {unread && (
                <span
                  className='size-2 shrink-0 rounded-full bg-accent'
                  aria-hidden='true'
                />
              )}
            </button>
          </li>
        );
      }),
    // `t` phải nằm trong mảng phụ thuộc: đổi ngôn ngữ thì react-i18next trả về
    // một `t` mới, thiếu nó thì danh sách đã memo hoá giữ nguyên chữ của ngôn
    // ngữ cũ cho tới khi có thứ khác kích hoạt tính lại.
    [newestMessages, user, handleOpenModal, t, isUserOnline]
  );

  return (
    <Popover
      open={Boolean(state.visibleMessagesDropdown)}
      onClose={closeAllDropdown}
      title={t('messages.title')}
    >
      {newestMessages?.messages?.length === 0 ? (
        <div className='flex flex-col items-center gap-2 px-4 py-10 text-center'>
          <FaRegComments className='size-6 text-fg-subtle' aria-hidden='true' />
          <p className='text-sm text-fg-muted'>{t('messages.empty')}</p>
        </div>
      ) : (
        <ul className='flex flex-col gap-0.5'>{memoMessages}</ul>
      )}
    </Popover>
  );
}

export default MessagesDropdown;
