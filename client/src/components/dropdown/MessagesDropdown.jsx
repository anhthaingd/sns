import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { formatDistanceStrict } from 'date-fns';
import { DropdownContext } from '../../context/NotificationProvider';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { ModalContext } from '../../context/ModalProvider';
import { useReadMessageMutation } from '../../services/redux/query/usersQuery';

function MessagesDropdown() {
  const { user, newestMessages, refetchMessages } =
    useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  const { state, closeAllDropdown } = useContext(DropdownContext);
  const [hoverMessage, setHoverMessage] = useState(null);
  const [readMessage, { isSuccess: isSuccessReadMessages }] =
    useReadMessageMutation();
  const handleOpenModal = useCallback(
    async (receiver, me, messId) => {
      setVisibleModal({ visibleChatModal: receiver?.user });
      closeAllDropdown();
      if (!me?.isRead) {
        await readMessage(messId);
      }
    },
    [setVisibleModal, closeAllDropdown, readMessage]
  );
  useEffect(() => {
    if (isSuccessReadMessages) {
      refetchMessages();
    }
  }, [isSuccessReadMessages]);
  const memoMessages = useMemo(() => {
    return newestMessages.messages?.map((m) => {
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
      return (
        <article
          key={m?._id}
          className={`p-2 flex gap-4 rounded cursor-pointer ${
            hoverMessage === m?._id ? 'bg-neutral-200 dark:bg-neutral-600' : ''
          }`}
          onMouseEnter={() => setHoverMessage(m?._id)}
          onMouseLeave={() => setHoverMessage(null)}
          onClick={() => handleOpenModal(receiver, me, m?._id)}
        >
          <div className='w-1/6 overflow-hidden'>
            <img
              className='size-[56px] rounded-full object-cover'
              src={`${import.meta.env?.VITE_BACKEND_URL}/${
                receiver?.user?.avatar?.url
              }`}
              alt={receiver?.user?.username}
              {...{ fetchPriority: 'low' }}
            />
          </div>
          <div className='relative w-5/6 text-base flex flex-col'>
            <p className='text-lg font-bold'>{receiver?.user?.username}</p>
            <div className='text-neutral-600 dark:text-neutral-300 font-bold flex items-center gap-2 pr-4'>
              <div className='flex gap-2'>
                {user._id === m?.lastSent && <p>You:</p>}
                <p
                  className={`max-w-[180px] w-full truncate ${
                    !me?.isRead ? 'dark:text-neutral-50 text-neutral-800' : ''
                  }`}
                >
                  {m?.content}
                </p>
              </div>
              <p className='text-[12px] flex'>
                {formatDistanceStrict(
                  new Date(Date.now()),
                  new Date(m?.updated_at)
                )}
              </p>
            </div>
            {!me?.isRead && (
              <span className='absolute w-2 h-2 rounded-full bg-blue-500 top-1/2 -translate-y-1/2 right-0'></span>
            )}
          </div>
        </article>
      );
    });
  }, [newestMessages, state.visibleMessagesDropdown]);
  return (
    <div
      className={`absolute w-[380px] right-0 my-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg overflow-hidden shadow-lg ${
        state.visibleMessagesDropdown ? 'h-[90vh]' : 'h-0'
      } transition-all duration-200 flex flex-col gap-4`}
    >
      <div className='p-4'>
        <h2 className='text-lg font-bold'>Messages</h2>
      </div>
      <div className='max-h-[80vh] overflow-y-auto'>
        {newestMessages?.messages?.length === 0 && (
          <div>
            <p>No Messages Yet!</p>
          </div>
        )}
        <div className='flex flex-col gap-4'>{memoMessages}</div>
      </div>
    </div>
  );
}

export default MessagesDropdown;
