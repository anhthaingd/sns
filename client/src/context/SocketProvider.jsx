import {
  createContext,
  useState,
  useRef,
  useEffect,
  useContext,
  useCallback,
} from 'react';
import { io } from 'socket.io-client';
import Peer from 'simple-peer';
import { ModalContext } from './ModalProvider';
import { FetchDataContext } from './FetchDataProvider';
import { getAccessToken } from '../services/utils/token';
export const SocketContext = createContext();

/**
 * Kết nối thời gian thực — giờ BẮT BUỘC mang access token.
 *
 * Máy chủ từ chối `connect` nếu không có token hợp lệ
 * (`server_python/app/sockets/handlers.py`). Trước đây socket mở ra ẩn danh và
 * mọi danh tính đều do client tự khai trong payload, nên gửi được tin nhắn
 * dưới tên người khác mà không cần đăng nhập.
 *
 * `auth` là HÀM chứ không phải object: socket.io gọi lại nó ở MỖI lần kết nối,
 * nên sau khi access token được gia hạn (15 phút một lần) thì lần kết nối lại
 * tự mang token mới — không phải tự tay dựng lại socket.
 *
 * `autoConnect: false`: chưa đăng nhập thì chưa có token, nối vào chỉ để bị từ
 * chối rồi thử lại vô ích.
 */
export const socket = io(import.meta.env.VITE_BACKEND_URL, {
  autoConnect: false,
  auth: (cb) => cb({ token: getAccessToken() || '' }),
});

export const SocketProvider = ({ children }) => {
  const [callAccepted, setCallAccepted] = useState(false);
  const { state, setVisibleModal } = useContext(ModalContext);
  const { refetchMessages } = useContext(FetchDataContext);
  const [callEnded, setCallEnded] = useState(false);
  const [stream, setStream] = useState(null);
  const [call, setCall] = useState({});
  const [me, setMe] = useState();
  const [receiver, setReceiver] = useState(null);

  // Phase 1: Thông báo real-time qua WebSocket.
  const [realtimeNotifications, setRealtimeNotifications] = useState([]);

  // Phase 4: Online presence — tập userId đang online.
  const [onlineUsers, setOnlineUsers] = useState(new Set());

  // Phase 4: Typing indicator — map senderId → boolean.
  const [typingUsers, setTypingUsers] = useState({});

  // Phase 5: System alert hiện tại (null = không có).
  const [systemAlert, setSystemAlert] = useState(null);

  // Phase 6: Cờ đánh dấu socket vừa reconnect → cần refetch notifications.
  const [socketReconnected, setSocketReconnected] = useState(false);

  const myVideo = useRef();
  const userVideo = useRef();
  const connectionRef = useRef();

  const myId = me?._id;
  useEffect(() => {
    if (!myId) {
      if (socket.connected) socket.disconnect();
      return undefined;
    }

    if (socket.connected) socket.disconnect();
    socket.connect();

    // ── Core ──────────────────────────────────────────────────────────

    const onConnect = () => {
      // Phase 3: Server tự join Room khi connect, không cần joinCall/joinChat
      // ghi DB nữa. Giữ emit joinCall cho backward compatibility (server handler
      // là no-op nhưng vẫn chấp nhận event).
      socket.emit('joinCall');

      // Phase 4: Hỏi danh sách user đang online.
      socket.emit('getOnlineUsers');
    };

    const onCallUser = (data) => setCall({ isReceivingCall: true, ...data });

    const onCallEnd = (data) => {
      if (data?.ended) setCallEnded(true);
    };

    // ── Phase 1: Thông báo real-time ──────────────────────────────────

    const onNotification = (data) => {
      setRealtimeNotifications((prev) => [data, ...prev]);
    };

    // ── Phase 2: Badge tin nhắn toàn cục ──────────────────────────────

    const onReceiveMessageGlobal = (message) => {
      if (message?.refetch) refetchMessages();
    };

    // ── Phase 4: Online presence ──────────────────────────────────────

    const onOnlineUsers = (data) => {
      setOnlineUsers(new Set(data?.userIds || []));
    };

    const onUserOnline = (data) => {
      if (data?.userId) {
        setOnlineUsers((prev) => new Set([...prev, data.userId]));
      }
    };

    const onUserOffline = (data) => {
      if (data?.userId) {
        setOnlineUsers((prev) => {
          const next = new Set(prev);
          next.delete(data.userId);
          return next;
        });
      }
    };

    // ── Phase 4: Typing indicator ─────────────────────────────────────

    const onTyping = (data) => {
      if (!data?.senderId) return;
      setTypingUsers((prev) => {
        if (data.isTyping) return { ...prev, [data.senderId]: true };
        const next = { ...prev };
        delete next[data.senderId];
        return next;
      });
    };

    // ── Phase 5: System alerts ────────────────────────────────────────

    const onSystemAlert = (data) => {
      setSystemAlert(data);
      // Tự ẩn sau thời gian nếu có expiresAt.
      if (data?.expiresAt) {
        const ms = new Date(data.expiresAt).getTime() - Date.now();
        if (ms > 0) setTimeout(() => setSystemAlert(null), ms);
      }
    };

    // ── Phase 6: Đánh dấu reconnect để refetch notifications ────────

    const onReconnect = () => {
      setSocketReconnected(true);
      socket.emit('getOnlineUsers');
    };

    // ── Đăng ký tất cả listeners ─────────────────────────────────────

    socket.on('connect', onConnect);
    socket.on('callUser', onCallUser);
    socket.on('callEnd', onCallEnd);
    socket.on('notification', onNotification);
    socket.on('receiveMessage', onReceiveMessageGlobal);
    socket.on('onlineUsers', onOnlineUsers);
    socket.on('userOnline', onUserOnline);
    socket.on('userOffline', onUserOffline);
    socket.on('typing', onTyping);
    socket.on('systemAlert', onSystemAlert);
    socket.io.on('reconnect', onReconnect);
    if (socket.connected) onConnect();

    return () => {
      socket.off('connect', onConnect);
      socket.off('callUser', onCallUser);
      socket.off('callEnd', onCallEnd);
      socket.off('notification', onNotification);
      socket.off('receiveMessage', onReceiveMessageGlobal);
      socket.off('onlineUsers', onOnlineUsers);
      socket.off('userOnline', onUserOnline);
      socket.off('userOffline', onUserOffline);
      socket.off('typing', onTyping);
      socket.off('systemAlert', onSystemAlert);
      socket.io.off('reconnect', onReconnect);
    };
  }, [myId, refetchMessages]);

  // ── Video call helpers (không thay đổi so với trước) ────────────────

  const ensureStream = useCallback(async () => {
    if (stream) return stream;
    if (!navigator.mediaDevices?.getUserMedia) {
      console.warn(
        'navigator.mediaDevices khong kha dung - can https hoac localhost. Goi video se bi tat.'
      );
      return null;
    }
    try {
      const current = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      setStream(current);
      return current;
    } catch (err) {
      console.warn('Khong truy cap duoc camera/mic:', err?.message);
      return null;
    }
  }, [stream]);

  useEffect(() => {
    if (state.visibleVideoModal || call.isReceivingCall) ensureStream();
  }, [state.visibleVideoModal, call.isReceivingCall, ensureStream]);

  useEffect(() => {
    if (stream && myVideo.current && state.visibleVideoModal) {
      myVideo.current.srcObject = stream;
    }
  }, [stream, myVideo.current, state.visibleVideoModal]);

  useEffect(() => {
    if (receiver && state.visibleVideoModal && !call.isReceivingCall) {
      callUser(receiver);
    }
  }, [receiver, state.visibleVideoModal, call]);

  const answerCall = async () => {
    const currentStream = await ensureStream();
    setCallAccepted(true);
    const peer = new Peer({ initiator: false, trickle: false, stream: currentStream });

    peer.on('signal', (data) => {
      socket.emit('answerCall', { signal: data, to: call.from });
    });

    peer.on('stream', (remoteStream) => {
      if (userVideo.current) userVideo.current.srcObject = remoteStream;
    });

    if (call.signal) {
      peer.signal(call.signal);
    }

    connectionRef.current = peer;
  };

  const callUser = async (target) => {
    setCallAccepted(false);
    setCallEnded(false);
    const currentStream = await ensureStream();
    if (!currentStream || !me) return;

    const peer = new Peer({ initiator: true, trickle: false, stream: currentStream });

    peer.on('signal', (data) => {
      socket.emit('callUser', { signalData: data, seeder: me, receiver: target });
    });

    peer.on('stream', (remoteStream) => {
      if (userVideo.current) userVideo.current.srcObject = remoteStream;
    });

    socket.once('callAccepted', (signal) => {
      setCallAccepted(true);
      peer.signal(signal);
    });

    connectionRef.current = peer;
  };

  const leaveCall = (target) => {
    socket.emit('callEnd', { receiver: target });
    setCallEnded(true);
    if (connectionRef.current) {
      connectionRef.current.destroy();
      connectionRef.current = null;
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    setCall({});
    setCallAccepted(false);
    setVisibleModal(null);
  };

  // ── Public helpers ──────────────────────────────────────────────────

  const clearRealtimeNotifications = useCallback(() => {
    setRealtimeNotifications([]);
  }, []);

  const clearSocketReconnected = useCallback(() => {
    setSocketReconnected(false);
  }, []);

  const dismissSystemAlert = useCallback(() => {
    setSystemAlert(null);
  }, []);

  const isUserOnline = useCallback(
    (userId) => onlineUsers.has(userId),
    [onlineUsers]
  );

  return (
    <SocketContext.Provider
      value={{
        call,
        callAccepted,
        myVideo,
        userVideo,
        stream,
        callEnded,
        me,
        setMe,
        receiver,
        setReceiver,
        callUser,
        leaveCall,
        answerCall,
        // Phase 1: Notifications
        realtimeNotifications,
        clearRealtimeNotifications,
        // Phase 4: Presence
        onlineUsers,
        isUserOnline,
        // Phase 4: Typing
        typingUsers,
        // Phase 5: System alerts
        systemAlert,
        dismissSystemAlert,
        // Phase 6: Reconnect flag
        socketReconnected,
        clearSocketReconnected,
      }}
    >
      {children}
    </SocketContext.Provider>
  );
};
