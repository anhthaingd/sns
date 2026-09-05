import Modal from '@/modal';
import { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { FaXmark, FaPaperPlane, FaVideo } from 'react-icons/fa6';
import { ModalContext } from '../../context/ModalProvider';
import { useNavigate } from 'react-router-dom';
import { socket } from '../../context/SocketProvider';

// Cuộn tới trong khoảng này tính từ đầu danh sách thì coi như "muốn xem tin cũ".
const LOAD_MORE_SCROLL_THRESHOLD_PX = 24;
import { useLazyGetChatQuery } from '../../services/redux/query/usersQuery';
function ChatModal() {
  const { user, refetchMessages } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [totalPage, setTotalPage] = useState(1);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [messages, setMessages] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isFocusCmt, setIsFocusCmt] = useState(false);
  const messageRef = useRef();
  const chatContainerRef = useRef();
  // Sau khi chèn tin cũ lên đầu thì KHÔNG được nhảy xuống đáy, phải giữ nguyên
  // chỗ người dùng đang đọc. Hai ref dưới điều khiển việc đó.
  const shouldScrollToBottomRef = useRef(true);
  const prevScrollHeightRef = useRef(0);
  // Guard bằng ref chứ không bằng state: `onScroll` bắn liên tục và state cập
  // nhật bất đồng bộ, nên chỉ dựa vào `isLoadingMore` sẽ tải trùng một trang.
  const isLoadingMoreRef = useRef(false);
  const [triggerGetChat] = useLazyGetChatQuery();
  const handleFocusComment = () => {
    if (messageRef.current) {
      messageRef.current.focus();
      setIsFocusCmt(true);
    }
  };

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

      socket.on('receiveMessage', (message) => {
        // Tin mới luôn nối xuống cuối -> cuộn xuống đáy.
        shouldScrollToBottomRef.current = true;
        setMessages((prevMessages) => [...prevMessages, message]);
        if (message.refetch) {
          refetchMessages();
        }
      });

      socket.emit('joinChat', user);

      return () => {
        socket.off('receiveMessage');
        socket.off('userConnected');
      };
    } else {
      setMessages([]);
    }
  }, [state.visibleChatModal]);

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

  const sendMessage = () => {
    if (!selectedUser || !messageRef?.current?.textContent) return;
    const messageData = {
      sender: user,
      receiver: selectedUser,
      content: messageRef?.current?.textContent,
      lastSent: user,
    };
    socket.emit('sendMessage', messageData);
    if (messageRef.current) {
      messageRef.current.textContent = '';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  return (
    <Modal>
      <section
        className={`fixed w-[320px] h-[465px] bg-neutral-50 dark:bg-neutral-800 z-50 bottom-0 right-4 border border-neutral-300 dark:border-neutral-500 rounded-lg dark:text-neutral-100 flex ${
          state.visibleChatModal ? 'flex' : 'hidden'
        } flex-col justify-between`}
      >
        <div className='p-2 flex justify-between items-center gap-4 border-b border-neutral-300 dark:border-neutral-500'>
          <div className='flex gap-4'>
            <img
              className='size-[36px] rounded-full object-cover'
              src={`${import.meta.env.VITE_BACKEND_URL}/${
                selectedUser?.avatar?.url
              }`}
              alt={selectedUser?.avatar?.name}
              {...{ fetchPriority: 'low' }}
            />
            <p
              className='font-bold cursor-pointer'
              onClick={() => {
                setVisibleModal('visibleChatModal');
                navigate(`/profile/${selectedUser?._id}`);
              }}
            >
              {selectedUser?.username}
            </p>
          </div>
          <div className='flex items-center gap-2'>
            <button
              title='Call Video'
              aria-label='call-video'
              onClick={() =>
                setVisibleModal({
                  visibleVideoModal: {
                    seeder: user,
                    receiver: selectedUser,
                  },
                })
              }
            >
              <FaVideo className='text-2xl rotate-180' />
            </button>
            <button
              title='Close chat'
              aria-label='close-chat'
              onClick={() => setVisibleModal('visibleChatModal')}
            >
              <FaXmark className='text-2xl' />
            </button>
          </div>
        </div>
        <div
          ref={chatContainerRef}
          onScroll={handleScroll}
          className='px-2 py-4 w-full h-full overflow-y-auto flex flex-col gap-4'
        >
          {isLoadingMore && (
            <p className='text-center text-xs opacity-60'>Đang tải tin cũ...</p>
          )}
          {messages?.map((m) => {
            const isSender = m?.sender?._id === user?._id;
            return (
              <div
                key={m._id}
                className={`w-full flex items-center gap-2 ${
                  isSender ? 'justify-end' : 'justify-start'
                }`}
              >
                {!isSender && (
                  <img
                    className='size-[36px] rounded-full object-cover'
                    src={`${import.meta.env.VITE_BACKEND_URL}/${
                      m?.sender?.avatar?.url
                    }`}
                    alt={m?.sender?.avatar?.name}
                    {...{ fetchPriority: 'low' }}
                  />
                )}
                <p
                  className={`max-w-[180px] px-2 py-1 rounded-3xl break-words ${
                    isSender
                      ? 'bg-blue-500 text-neutral-100'
                      : 'bg-neutral-200 dark:bg-neutral-700'
                  }`}
                >
                  {m?.content}
                </p>
              </div>
            );
          })}
        </div>
        <div className='relative w-full p-2' onClick={handleFocusComment}>
          <p
            onBlur={() => {
              setIsFocusCmt(false);
            }}
            onKeyDown={handleKeyDown}
            ref={messageRef}
            className='rounded-3xl px-4 py-2 bg-neutral-200 dark:bg-neutral-700 max-h-[180px] focus:outline overflow-y-auto'
            contentEditable
          ></p>
          {!isFocusCmt && !messageRef.current?.textContent && (
            <div
              className='absolute top-1/2 left-6 -translate-y-1/2'
              onClick={handleFocusComment}
            >
              <p>Aa</p>
            </div>
          )}
          <button
            className='absolute bottom-[35%] right-6 z-10 hover:text-blue-500 transition-colors'
            aria-label='send-btn'
            disabled={!messageRef.current?.textContent}
            onClick={sendMessage}
          >
            <FaPaperPlane />
          </button>
        </div>
      </section>
    </Modal>
  );
}

export default ChatModal;
