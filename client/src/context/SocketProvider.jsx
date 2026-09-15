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
  const [callEnded, setCallEnded] = useState(false);
  const [stream, setStream] = useState(null);
  const [call, setCall] = useState({});
  const [me, setMe] = useState();
  const [receiver, setReceiver] = useState(null);

  const myVideo = useRef();
  const userVideo = useRef();
  const connectionRef = useRef();

  // Mở kết nối khi đã đăng nhập, đóng khi đăng xuất. `me` được gán từ `App.jsx`
  // ngay khi có thông tin người dùng.
  //
  // Phụ thuộc là `me?._id` chứ không phải cả object `me`: `getByToken` được gọi
  // lại khá thường xuyên và trả về object MỚI mỗi lần, nên bám vào `me` sẽ
  // ngắt/nối socket liên tục.
  const myId = me?._id;
  useEffect(() => {
    if (!myId) {
      if (socket.connected) socket.disconnect();
      return undefined;
    }

    // Đổi danh tính thì BẮT BUỘC nối lại: `auth` chỉ được đánh giá lúc bắt tay,
    // nên một socket đang mở vẫn mang danh tính của người đăng nhập trước đó.
    // Dùng lại nó thì `joinCall`/`joinChat` sẽ gán socket này cho nhầm người.
    if (socket.connected) socket.disconnect();
    socket.connect();

    const onConnect = () => socket.emit('joinCall');
    const onCallUser = (data) => setCall({ isReceivingCall: true, ...data });
    // Máy chủ gửi `ended: true`. Bản cũ kiểm `data.receiver.socketCallId` —
    // một trường chưa bao giờ có trong gói tin — nên phía người nhận KHÔNG BAO
    // GIỜ biết là cuộc gọi đã kết thúc.
    const onCallEnd = (data) => {
      if (data?.ended) setCallEnded(true);
    };

    socket.on('connect', onConnect);
    socket.on('callUser', onCallUser);
    socket.on('callEnd', onCallEnd);
    if (socket.connected) onConnect();

    // Gỡ listener khi dọn: thiếu bước này thì mỗi lần `me` đổi là chồng thêm
    // một bộ listener nữa, và một cuộc gọi tới sẽ kích hoạt nhiều lần.
    return () => {
      socket.off('connect', onConnect);
      socket.off('callUser', onCallUser);
      socket.off('callEnd', onCallEnd);
    };
  }, [myId]);

  /**
   * Xin quyền camera/micro — CHỈ khi thực sự sắp gọi.
   *
   * Bản cũ gọi `getUserMedia` ngay trong effect của `me`, tức là mọi người vừa
   * đăng nhập là bị trình duyệt hỏi quyền camera + micro, kể cả người không
   * bao giờ dùng gọi video.
   */
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

  // Mở khung gọi video (dù là gọi đi hay nhận cuộc gọi) mới xin quyền thiết bị.
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
      // Dữ liệu signal của WebRTC KHÔNG được log ra console: nó là mô tả phiên
      // của cuộc gọi, và console là nơi ai ngồi trước máy cũng đọc được.
      socket.emit('callUser', { signalData: data, seeder: me, receiver: target });
    });

    peer.on('stream', (remoteStream) => {
      if (userVideo.current) userVideo.current.srcObject = remoteStream;
    });

    // `once` chứ không phải `on`: bản cũ đăng ký listener mới ở MỖI lần gọi mà
    // không bao giờ gỡ, nên cuộc gọi thứ n có n listener cùng chạy.
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
    // Tắt camera/micro thật sự. Bản cũ dựa vào `window.location.reload()` để
    // dọn — tải lại toàn bộ ứng dụng chỉ để kết thúc một cuộc gọi, làm mất mọi
    // trạng thái đang mở và nháy trắng cả màn hình.
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    setCall({});
    setCallAccepted(false);
    setVisibleModal(null);
  };
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
      }}
    >
      {children}
    </SocketContext.Provider>
  );
};
