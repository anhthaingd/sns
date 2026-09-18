import Modal from '@/modal';
import { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaXmark, FaPaperPlane, FaVideo, FaMinus } from 'react-icons/fa6';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { ModalContext } from '../../context/ModalProvider';
import { socket, SocketContext } from '../../context/SocketProvider';
import { useLazyGetChatQuery } from '../../services/redux/query/api/chatApi';
import Avatar from '../ui/Avatar';
import IconButton from '../ui/IconButton';
import Spinner from '../ui/Spinner';
import cn from '../../services/utils/cn';

// Cuộn tới trong khoảng này tính từ đầu danh sách thì coi như "muốn xem tin cũ".
const LOAD_MORE_SCROLL_THRESHOLD_PX = 24;

// Debounce gõ: gửi typing=true khi bắt đầu gõ, typing=false sau khi ngừng 2s.
const TYPING_DEBOUNCE_MS = 2000;

function ChatModal() {
  const { t } = useTranslation('chat');
  const { user } = useContext(FetchDataContext);
  const { typingUsers, isUserOnline } = useContext(SocketContext);
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [totalPage, setTotalPage] = useState(1);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [messages, setMessages] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [draft, setDraft] = useState('');
  const [minimized, setMinimized] = useState(false);
  const chatContainerRef = useRef();
  // Sau khi chèn tin cũ lên đầu thì KHÔNG được nhảy xuống đáy, phải giữ nguyên
  // chỗ người dùng đang đọc. Hai ref dưới điều khiển việc đó.
  const shouldScrollToBottomRef = useRef(true);
  const prevScrollHeightRef = useRef(0);
  // Guard bằng ref chứ không bằng state: `onScroll` bắn liên tục và state cập
  // nhật bất đồng bộ, nên chỉ dựa vào `isLoadingMore` sẽ tải trùng một trang.
  const isLoadingMoreRef = useRef(false);
  const typingTimerRef = useRef(null);
  const [triggerGetChat] = useLazyGetChatQuery();

  // Phase 4: Emit typing indicator khi người dùng gõ.
  const emitTyping = useCallback(
    (isTyping) => {
      if (!selectedUser?._id) return;
      socket.emit('typing', { receiverId: selectedUser._id, isTyping });
    },
    [selectedUser?._id]
  );

  const handleTyping = useCallback(() => {
    emitTyping(true);
    clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => emitTyping(false), TYPING_DEBOUNCE_MS);
  }, [emitTyping]);

  // Đi qua RTK Query (thay vì `fetch` thô) để dùng chung cơ chế tự gia hạn
  // access token; trước đây token hết hạn giữa chừng là khung chat trắng xoá.
  const loadMessages = useCallback(
    async (targetPage, { prepend = false } = {}) => {
      if (!user?._id || !selectedUser?._id) return;
      try {
        const data = await triggerGetChat({
          senderId: user._id,
          receiverId: selectedUser._id,
          page: targetPage,
        }).unwrap();
        setTotalPage(data?.totalPage || 1);
        setMessages((prev) =>
          prepend ? [...(data?.messages || []), ...prev] : data?.messages || []
        );
      } catch (error) {
        console.error('Error fetching messages', error);
      }
    },
    [user?._id, selectedUser?._id, triggerGetChat]
  );

  // Cuộn tới gần đầu danh sách -> tải trang cũ hơn.
  const handleScroll = useCallback(async () => {
    const container = chatContainerRef.current;
    if (!container || isLoadingMoreRef.current) return;
    if (container.scrollTop > LOAD_MORE_SCROLL_THRESHOLD_PX || page >= totalPage)
      return;

    isLoadingMoreRef.current = true;
    prevScrollHeightRef.current = container.scrollHeight;
    shouldScrollToBottomRef.current = false;
    setIsLoadingMore(true);
    const nextPage = page + 1;
    try {
      await loadMessages(nextPage, { prepend: true });
      setPage(nextPage);
    } finally {
      isLoadingMoreRef.current = false;
      setIsLoadingMore(false);
    }
  }, [page, totalPage, loadMessages]);

  useEffect(() => {
    if (state.visibleChatModal) {
      setMessages([]);
      setSelectedUser(state.visibleChatModal);
      setPage(1);
      setTotalPage(1);
      setMinimized(false);

      const partnerId = state.visibleChatModal?._id;

      const onReceive = (message) => {
        // CHỈ nhận tin thuộc đúng hội thoại đang mở.
        //
        // Bản cũ nối thẳng mọi tin nhận được vào danh sách, nên đang chat với B
        // mà C nhắn tới thì tin của C hiện luôn trong khung của B — vừa sai
        // ngữ cảnh vừa là rò rỉ nội dung sang nhầm cửa sổ.
        const from = message?.sender?._id;
        const to = message?.receiver?._id;
        const inThisConversation =
          (from === partnerId && to === user?._id) ||
          (from === user?._id && to === partnerId);

        // Badge tin nhắn (refetchMessages) giờ được xử lý ở tầng global trong
        // SocketProvider — không cần gọi lại ở đây nữa.
        if (!inThisConversation) return;

        // Tin mới luôn nối xuống cuối -> cuộn xuống đáy.
        shouldScrollToBottomRef.current = true;
        setMessages((prevMessages) => [...prevMessages, message]);
      };

      socket.on('receiveMessage', onReceive);
      socket.emit('joinChat');

      return () => {
        socket.off('receiveMessage', onReceive);
      };
    }
    setMessages([]);
    return undefined;
  }, [state.visibleChatModal, user?._id]);

  useEffect(() => {
    if (state.visibleChatModal && selectedUser) {
      setMessages([]);
      setPage(1);
      isLoadingMoreRef.current = false;
      shouldScrollToBottomRef.current = true;
      loadMessages(1);
    }
  }, [state.visibleChatModal, selectedUser, loadMessages]);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;
    if (shouldScrollToBottomRef.current) {
      container.scrollTop = container.scrollHeight;
      return;
    }
    // Vừa chèn tin cũ lên đầu: bù đúng phần chiều cao mới thêm vào để nội dung
    // người dùng đang nhìn không bị nhảy.
    container.scrollTop = container.scrollHeight - prevScrollHeightRef.current;
    shouldScrollToBottomRef.current = true;
  }, [messages]);

  // Ô nhập là <textarea> thật, không phải <p contentEditable> vẽ placeholder
  // bằng tay như bản cũ: bộ gõ tiếng Nhật (IME) hoạt động đúng, và nút gửi
  // biết được ô có rỗng hay không ngay khi gõ — trước đây `disabled` đọc
  // `messageRef.current?.textContent` nên chỉ đúng sau lần render kế tiếp.
  const sendMessage = () => {
    const content = draft.trim();
    if (!selectedUser || !content) return;
    socket.emit('sendMessage', {
      receiver: { _id: selectedUser?._id },
      content,
    });
    setDraft('');
    // Ngừng typing khi gửi xong.
    emitTyping(false);
    clearTimeout(typingTimerRef.current);
  };

  // Phase 4: Người đối diện có đang gõ không?
  const partnerIsTyping = selectedUser?._id && typingUsers[selectedUser._id];
  const partnerIsOnline = selectedUser?._id && isUserOnline(selectedUser._id);

  if (!state.visibleChatModal) return null;

  return (
    <Modal>
      <section
        className={cn(
          'fixed bottom-0 right-2 z-50 flex w-[min(21rem,calc(100vw-1rem))] animate-rise flex-col',
          'overflow-hidden rounded-t-card bg-surface shadow-modal ring-1 ring-inset ring-line sm:right-4',
          minimized ? 'h-auto' : 'h-[28rem] max-h-[75vh]'
        )}
      >
        <header className='flex shrink-0 items-center gap-2 border-b border-line bg-surface-2 px-3 py-2'>
          <button
            type='button'
            className='flex min-w-0 flex-1 items-center gap-2.5 text-left'
            onClick={() => {
              setVisibleModal('visibleChatModal');
              navigate(`/profile/${selectedUser?._id}`);
            }}
          >
            <Avatar
              src={selectedUser?.avatar}
              name={selectedUser?.username}
              size='sm'
              status={partnerIsOnline ? 'online' : undefined}
            />
            <span className='min-w-0'>
              <span className='block truncate text-sm font-bold text-fg'>
                {selectedUser?.username}
              </span>
              {partnerIsOnline && (
                <span className='block text-2xs text-success'>
                  {partnerIsTyping ? t('modal.typing') : t('modal.online')}
                </span>
              )}
            </span>
          </button>
          <IconButton
            size='sm'
            label={t('modal.videoCall')}
            onClick={() =>
              setVisibleModal({
                visibleVideoModal: { seeder: user, receiver: selectedUser },
              })
            }
          >
            <FaVideo className='size-4' />
          </IconButton>
          <IconButton
            size='sm'
            label={minimized ? t('modal.open') : t('modal.minimize')}
            onClick={() => setMinimized((v) => !v)}
          >
            <FaMinus className='size-4' />
          </IconButton>
          <IconButton
            size='sm'
            label={t('modal.close')}
            onClick={() => setVisibleModal('visibleChatModal')}
          >
            <FaXmark className='size-4' />
          </IconButton>
        </header>

        {!minimized && (
          <>
            <div
              ref={chatContainerRef}
              onScroll={handleScroll}
              className='flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto overscroll-contain px-3 py-3'
            >
              {isLoadingMore && (
                <p className='flex items-center justify-center gap-2 py-1 text-2xs text-fg-subtle'>
                  <Spinner className='size-3' />
                  {t('modal.loadingOlder')}
                </p>
              )}
              {messages?.length === 0 && !isLoadingMore && (
                <p className='py-6 text-center text-sm text-fg-muted'>
                  {t('modal.noMessages')}
                </p>
              )}
              {messages?.map((m, index) => {
                const isSender = m?.sender?._id === user?._id;
                return (
                  <div
                    // Tin tới qua socket chưa có `_id` (chưa đọc lại từ DB), nên
                    // chỉ dùng `_id` thì mọi tin mới đều có key `undefined` và
                    // React coi chúng là cùng một phần tử.
                    key={m._id || `${m?.timestamp || 'new'}-${index}`}
                    className={cn(
                      'flex items-end gap-2',
                      isSender ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {!isSender && (
                      <Avatar
                        src={m?.sender?.avatar}
                        name={m?.sender?.username}
                        size='xs'
                      />
                    )}
                    <p
                      className={cn(
                        'max-w-[75%] whitespace-pre-wrap break-words rounded-2xl px-3 py-1.5 text-sm',
                        isSender
                          ? 'rounded-br-sm bg-brand text-brand-on'
                          : 'rounded-bl-sm bg-surface-2 text-fg'
                      )}
                    >
                      {m?.content}
                    </p>
                  </div>
                );
              })}
              {partnerIsTyping && (
                <div className='flex items-end gap-2'>
                  <Avatar
                    src={selectedUser?.avatar}
                    name={selectedUser?.username}
                    size='xs'
                  />
                  <span className='rounded-2xl rounded-bl-sm bg-surface-2 px-3 py-1.5 text-sm text-fg-muted'>
                    <span className='inline-flex gap-0.5'>
                      <span className='size-1.5 animate-bounce rounded-full bg-fg-subtle [animation-delay:0ms]' />
                      <span className='size-1.5 animate-bounce rounded-full bg-fg-subtle [animation-delay:150ms]' />
                      <span className='size-1.5 animate-bounce rounded-full bg-fg-subtle [animation-delay:300ms]' />
                    </span>
                  </span>
                </div>
              )}
            </div>

            <div className='shrink-0 border-t border-line p-2'>
              <div className='relative'>
                <textarea
                  rows={1}
                  className='max-h-24 w-full resize-none rounded-2xl bg-surface-2 py-2 pl-3 pr-10 text-sm text-fg ring-1 ring-inset ring-transparent transition-shadow placeholder:text-fg-subtle focus:bg-surface focus:ring-accent'
                  placeholder={t('modal.inputPlaceholder')}
                  value={draft}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    handleTyping();
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                />
                <button
                  type='button'
                  className='absolute bottom-1.5 right-1.5 flex size-7 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-accent-soft hover:text-accent-text disabled:opacity-40'
                  aria-label={t('modal.send')}
                  disabled={!draft.trim()}
                  onClick={sendMessage}
                >
                  <FaPaperPlane className='size-3.5' />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </Modal>
  );
}

export default ChatModal;
