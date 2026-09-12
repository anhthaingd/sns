import { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  FaXmark,
  FaPhone,
  FaVideo,
  FaMicrophone,
  FaMicrophoneSlash,
  FaVideoSlash,
} from 'react-icons/fa6';
import { ModalContext } from '../../context/ModalProvider';
import { SocketContext } from '../../context/SocketProvider';
import Avatar from '../ui/Avatar';
import Button from '../ui/Button';
import cn from '../../services/utils/cn';

/** Nút tròn trong thanh điều khiển cuộc gọi. */
function CallButton({ label, tone = 'neutral', onClick, children }) {
  const tones = {
    neutral: 'bg-white/15 text-white hover:bg-white/25',
    active: 'bg-warning text-ai-950 hover:brightness-110',
    danger: 'bg-danger text-white hover:bg-shu-600',
  };
  return (
    <button
      type='button'
      aria-label={label}
      title={label}
      className={cn(
        'flex size-12 items-center justify-center rounded-full text-lg transition-all duration-150 active:scale-95',
        tones[tone]
      )}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function VideoModal() {
  const { t } = useTranslation(['chat', 'common']);
  const { state, setVisibleModal } = useContext(ModalContext);
  const {
    call,
    callAccepted,
    myVideo,
    userVideo,
    stream,
    callEnded,
    receiver,
    setReceiver,
    leaveCall,
    answerCall,
  } = useContext(SocketContext);

  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);

  useEffect(() => {
    setReceiver(state.visibleVideoModal ? state.visibleVideoModal?.receiver : null);
  }, [state.visibleVideoModal, setReceiver, call]);

  useEffect(() => {
    if (stream) {
      const audioTrack = stream.getAudioTracks()[0];
      const videoTrack = stream.getVideoTracks()[0];
      setIsMuted(!audioTrack.enabled);
      setIsVideoOff(!videoTrack.enabled);
    }
  }, [stream]);

  const toggleMute = () => {
    if (!stream) return;
    const audioTrack = stream.getAudioTracks()[0];
    audioTrack.enabled = !audioTrack.enabled;
    setIsMuted(!audioTrack.enabled);
  };

  const toggleVideo = () => {
    if (!stream) return;
    const videoTrack = stream.getVideoTracks()[0];
    videoTrack.enabled = !videoTrack.enabled;
    setIsVideoOff(!videoTrack.enabled);
  };

  if (!state.visibleVideoModal) return null;

  const remoteLive = callAccepted && !callEnded;

  return (
    // Cuộc gọi luôn dùng nền tối, kể cả khi giao diện đang ở chế độ sáng: khung
    // hình camera nổi lên rõ nhất trên nền tối, và đó cũng là quy ước chung của
    // mọi ứng dụng gọi video.
    <section className='fixed inset-0 z-[100] flex animate-fade-in flex-col bg-ai-950/95 backdrop-blur-sm'>
      <header className='flex items-center justify-between gap-4 px-4 py-3'>
        <p className='truncate text-sm font-semibold text-white/80'>
          {receiver?.username}
        </p>
        <button
          type='button'
          className='rounded-full p-2 text-white/70 transition-colors hover:bg-white/10 hover:text-white'
          aria-label={t('video.close')}
          onClick={() => leaveCall(receiver)}
        >
          <FaXmark className='size-5' />
        </button>
      </header>

      <div className='relative mx-auto w-full max-w-5xl flex-1 px-4'>
        {/* Khung lớn: người bên kia. Khi chưa nối máy thì là ảnh đại diện. */}
        <div className='relative flex size-full items-center justify-center overflow-hidden rounded-card bg-ai-900 ring-1 ring-inset ring-white/10'>
          {remoteLive ? (
            <video className='size-full object-cover' playsInline ref={userVideo} autoPlay />
          ) : (
            <div className='flex flex-col items-center gap-4 text-center'>
              <Avatar src={receiver?.avatar} name={receiver?.username} size='2xl' />
              <p className='text-lg font-bold text-white'>{receiver?.username}</p>
              <p className='text-sm text-white/60'>
                {callEnded ? t('video.ended') : t('video.calling')}
              </p>
            </div>
          )}

          {/* Khung nhỏ: camera của mình, lồng vào góc thay vì chia đôi màn hình
              như bản cũ — mình chỉ cần liếc qua để biết mình có trong khung. */}
          {stream && (
            <div className='absolute bottom-4 right-4 w-32 overflow-hidden rounded-xl bg-ai-950 shadow-modal ring-1 ring-inset ring-white/20 sm:w-48'>
              <video
                className='aspect-[4/3] w-full object-cover'
                playsInline
                muted
                ref={myVideo}
                autoPlay
              />
            </div>
          )}
        </div>
      </div>

      <footer className='flex flex-col items-center gap-4 px-4 py-6'>
        {call?.isReceivingCall && !callAccepted && (
          <>
            <p className='text-sm text-white/80'>
              {t('video.incoming', { name: call.from.username })}
            </p>
            <Button variant='accent' size='lg' icon={FaVideo} onClick={answerCall}>
              {t('video.answer')}
            </Button>
          </>
        )}

        {!callEnded && (
          <div className='flex items-center gap-4'>
            <CallButton
              label={t('video.toggleMute')}
              tone={isMuted ? 'active' : 'neutral'}
              onClick={toggleMute}
            >
              {isMuted ? <FaMicrophoneSlash /> : <FaMicrophone />}
            </CallButton>
            <CallButton
              label={t('video.cancel')}
              tone='danger'
              onClick={() => leaveCall(receiver)}
            >
              <FaPhone className='rotate-[135deg]' />
            </CallButton>
            <CallButton
              label={t('video.toggleVideo')}
              tone={isVideoOff ? 'active' : 'neutral'}
              onClick={toggleVideo}
            >
              {isVideoOff ? <FaVideoSlash /> : <FaVideo />}
            </CallButton>
          </div>
        )}

        {/* Cuộc gọi kết thúc thì phải có đường thoát. Bản cũ để trống hoàn toàn
            nhánh này (nút đóng bị comment lại), nên màn hình "đã kết thúc" kẹt
            lại cho tới khi tải lại trang. */}
        {callEnded && (
          <Button variant='outline' onClick={() => setVisibleModal('visibleVideoModal')}>
            {t('video.close')}
          </Button>
        )}
      </footer>
    </section>
  );
}

export default VideoModal;
