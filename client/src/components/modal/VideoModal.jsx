import React, { useContext, useEffect, useState } from 'react';
import { ModalContext } from '../../context/ModalProvider';
import {
  FaXmark,
  FaPhone,
  FaVideo,
  FaMicrophone,
  FaMicrophoneSlash,
  FaVideoSlash,
} from 'react-icons/fa6';
import { SocketContext } from '../../context/SocketProvider';

function VideoModal() {
  const { state } = useContext(ModalContext);
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
    if (state.visibleVideoModal) {
      setReceiver(state.visibleVideoModal?.receiver);
    } else {
      setReceiver(null);
    }
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
    if (stream) {
      const audioTrack = stream.getAudioTracks()[0];
      audioTrack.enabled = !audioTrack.enabled;
      setIsMuted(!audioTrack.enabled);
    }
  };

  const toggleVideo = () => {
    if (stream) {
      const videoTrack = stream.getVideoTracks()[0];
      videoTrack.enabled = !videoTrack.enabled;
      setIsVideoOff(!videoTrack.enabled);
    }
  };

  return (
    <section
      style={{ backgroundColor: 'rgba(51,51,51,0.9)' }}
      className={`fixed right-0 top-0 w-full h-full z-[100] justify-center items-center overflow-hidden transition-all duration-200 ${
        state.visibleVideoModal ? 'flex' : 'hidden'
      }`}
    >
      <div className='bg-neutral-800 text-neutral-100 border border-neutral-600 w-3/5 h-[80vh] py-4 px-6 rounded-lg flex flex-col gap-[26px]'>
        <div className='w-full flex justify-end'>
          <button aria-label='close-modal' onClick={() => leaveCall(receiver)}>
            <FaXmark className='text-2xl' />
          </button>
        </div>
        <div className='h-full p-8 flex flex-col justify-center items-center'>
          <div className='w-full h-full grid grid-cols-2 gap-8'>
            {(!callAccepted || callEnded) && (
              <div className='col-span-1 flex flex-col items-center justify-center gap-4 border border-neutral-600 rounded'>
                <div className='w-24 h-24 rounded-full overflow-hidden'>
                  <img
                    className='w-full h-full object-cover'
                    src={`${import.meta.env.VITE_BACKEND_URL}/${
                      receiver?.avatar?.url
                    }`}
                    alt={receiver?.username}
                  />
                </div>
                <p className='text-lg font-bold'>{receiver?.username}</p>
                {!callEnded ? (
                  <p className='font-bold'>...Calling</p>
                ) : (
                  <p className='font-bold'>Call ended</p>
                )}
              </div>
            )}
            {callAccepted && !callEnded && (
              <div className='col-span-1 flex flex-col items-center justify-center gap-4 border border-neutral-600 rounded'>
                <video
                  className='w-full h-full'
                  playsInline
                  ref={userVideo}
                  autoPlay
                />
              </div>
            )}
            {stream && (
              <div className='col-span-1 border border-neutral-600 rounded'>
                <video
                  className='w-full h-full'
                  playsInline
                  muted
                  ref={myVideo}
                  autoPlay
                />
              </div>
            )}
          </div>
          <div className='mt-16 w-full flex justify-center items-center gap-8'>
            {!callEnded && (
              <>
                <button
                  className='bg-red-500 text-white rounded-full p-3 flex justify-center items-center'
                  aria-label='cancel'
                  onClick={() => leaveCall(receiver)}
                >
                  <FaPhone className='text-2xl rotate-[135deg]' />
                </button>
                <button
                  className='bg-yellow-500 text-white rounded-full p-3 flex justify-center items-center'
                  aria-label='toggle-mute'
                  onClick={toggleMute}
                >
                  {isMuted ? (
                    <FaMicrophoneSlash className='text-2xl' />
                  ) : (
                    <FaMicrophone className='text-2xl' />
                  )}
                </button>
                <button
                  className='bg-blue-500 text-white rounded-full p-3 flex justify-center items-center'
                  aria-label='toggle-video'
                  onClick={toggleVideo}
                >
                  {isVideoOff ? (
                    <FaVideoSlash className='text-2xl' />
                  ) : (
                    <FaVideo className='text-2xl' />
                  )}
                </button>
              </>
            )}
            {call?.isReceivingCall && !callAccepted && (
              <h1>{call.from.username} is calling:</h1>
            )}
            {call?.isReceivingCall && !callAccepted && (
              <button
                className='bg-green-500 text-white rounded-full p-3 flex justify-center items-center'
                onClick={answerCall}
              >
                Answer
              </button>
            )}
            {callEnded && (
              <div className='flex items-center gap-4'>
                {/* <button
                  className='bg-green-500 text-white rounded-full p-3 flex justify-center items-center'
                  aria-label='call'
                  onClick={() => callUser(receiver)}
                >
                  <FaVideo className='text-2xl' />
                </button> */}
                {/* <button
                  className='bg-neutral-400 text-white rounded-full p-3 flex justify-center items-center'
                  aria-label='close-modal'
                  onClick={() => setVisibleModal('visibleVideoModal')}
                >
                  <FaXmark className='text-2xl' />
                </button> */}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export default VideoModal;
