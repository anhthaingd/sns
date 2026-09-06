import {
  createContext,
  useState,
  useRef,
  useEffect,
  useContext,
} from 'react';
import { io } from 'socket.io-client';
import Peer from 'simple-peer';
import { ModalContext } from './ModalProvider';
export const SocketContext = createContext();

export const socket = io(import.meta.env.VITE_BACKEND_URL);

export const SocketProvider = ({ children }) => {
  const [callAccepted, setCallAccepted] = useState(false);
  const { state } = useContext(ModalContext);
  const [callEnded, setCallEnded] = useState(false);
  const [stream, setStream] = useState(null);
  const [call, setCall] = useState({});
  const [me, setMe] = useState();
  const [receiver, setReceiver] = useState(null);

  const myVideo = useRef();
  const userVideo = useRef();
  const connectionRef = useRef();

  useEffect(() => {
    if (me) {
      // navigator.mediaDevices chỉ tồn tại trong secure context (https/localhost),
      // và user có thể từ chối quyền camera/mic. Trước đây lỗi ở đây làm crash cả app.
      if (navigator.mediaDevices?.getUserMedia) {
        navigator.mediaDevices
          .getUserMedia({ video: true, audio: true })
          .then((currentStream) => {
            setStream(currentStream);
          })
          .catch((err) => {
            console.warn('Khong truy cap duoc camera/mic:', err?.message);
          });
      } else {
        console.warn(
          'navigator.mediaDevices khong kha dung - can https hoac localhost. Goi video se bi tat.'
        );
      }

      socket.emit('joinCall', me);

      socket.on('callUser', (data) => {
        console.log(data);
        setCall({ isReceivingCall: true, ...data });
      });
      socket.on('callEnd', (data) => {
        console.log(data);
        if (data?.receiver?.socketCallId) {
          setCallEnded(true);
        }
      });
    }
  }, [me]);
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
  const answerCall = () => {
    setCallAccepted(true);
    const peer = new Peer({ initiator: false, trickle: false, stream });

    peer.on('signal', (data) => {
      console.log(data);
      socket.emit('answerCall', { signal: data, to: call.from });
    });

    peer.on('stream', (currentStream) => {
      userVideo.current.srcObject = currentStream;
    });

    if (call.signal) {
      peer.signal(call.signal);
    }

    connectionRef.current = peer;
  };
  const callUser = (receiver) => {
    setCallAccepted(false);
    setCallEnded(false);
    if (!stream || !me) {
      console.error('Stream or me is not defined');
      return;
    }

    const peer = new Peer({ initiator: true, trickle: false, stream });
    console.log('Peer created:', peer);

    peer.on('signal', (data) => {
      console.log('Signal data:', data);
      socket.emit('callUser', {
        signalData: data,
        seeder: me,
        receiver: receiver,
      });
    });

    peer.on('stream', (currentStream) => {
      console.log('Received stream:', currentStream);
      userVideo.current.srcObject = currentStream;
    });

    socket.on('callAccepted', (signal) => {
      console.log('Call accepted, signal:', signal);
      if (!callAccepted) {
        setCallAccepted(true);
        peer.signal(signal);
      }
    });

    connectionRef.current = peer;
  };

  const leaveCall = (receiver) => {
    socket.emit('callEnd', { receiver: receiver });
    setCallEnded(true);
    if (connectionRef.current) {
      connectionRef.current.destroy();
    }
    window.location.reload();
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
