import Modal from '@/modal';
import { useContext, useEffect, useRef, useState } from 'react';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { FaXmark, FaPaperPlane, FaVideo } from 'react-icons/fa6';
import { ModalContext } from '../../context/ModalProvider';
import { getAccessToken } from '../../services/utils/token';
import { useNavigate } from 'react-router-dom';
import { socket } from '../../context/SocketProvider';
function ChatModal() {
  const { user, refetchMessages } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [messages, setMessages] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isFocusCmt, setIsFocusCmt] = useState(false);
  const messageRef = useRef();
  const chatContainerRef = useRef();
  const handleFocusComment = () => {
    if (messageRef.current) {
      messageRef.current.focus();
      setIsFocusCmt(true);
    }
  };

  const fetchMessagesData = async () => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_BACKEND_URL}/api/messages/${user._id}/${
          selectedUser._id
        }?page=${page}`,
        {
          headers: {
            Authorization: `Bearer ${getAccessToken()}`,
          },
        }
      );
      const data = await res.json();
      setMessages(data?.messages);
    } catch (error) {
      console.error('Error fetching messages', error);
    }
  };

  useEffect(() => {
    if (state.visibleChatModal) {
      setMessages([]);
      setSelectedUser(state.visibleChatModal);
      setPage(1);

      socket.on('receiveMessage', (message) => {
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
      fetchMessagesData();
    }
  }, [state.visibleChatModal, selectedUser]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
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
          className='px-2 py-4 w-full h-full overflow-y-auto flex flex-col gap-4'
        >
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
