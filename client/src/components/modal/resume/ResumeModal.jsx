import Modal from '@/modal';
import React, { useContext, useMemo, useRef, useState } from 'react';
import { FaXmark } from 'react-icons/fa6';
import { ModalContext } from '../../../context/ModalProvider';
import useClickOutside from '../../../hooks/useClickOutside';
import Template1 from './Template1';
import Template2 from './Template2';
function ResumeModal() {
  const { state, setVisibleModal } = useContext(ModalContext);
  const [modalRef, clickOutside] = useClickOutside();
  const [curTemplate, setCurTemplate] = useState('1');
  const form = useMemo(() => {
    return state.visibleResumeModal || {};
  }, [state.visibleResumeModal]);
  return (
    <Modal>
      <section
        style={{ backgroundColor: 'rgba(51,51,51,0.9)' }}
        className={`fixed overflow-y-auto right-0 top-0 w-full h-full z-[100] transition-all duration-200 py-8 px-4 ${
          state.visibleResumeModal ? 'block' : 'hidden'
        } `}
        onClick={clickOutside}
      >
        <div
          ref={modalRef}
          className='w-full xl:w-1/2 container m-auto flex flex-col gap-4 overflow-y-auto bg-white dark:bg-neutral-800 p-8 rounded'
        >
          <div className='px-4 w-full flex justify-end items-center'>
            <button onClick={() => setVisibleModal('visibleResumeModal')}>
              <FaXmark className='text-2xl dark:text-neutral-100' />
            </button>
          </div>
          <div className='p-4 flex items-center gap-4'>
            <button
              className={`${
                curTemplate === '1'
                  ? 'bg-neutral-700 text-white'
                  : 'border border-neutral-300 text-neutral-700'
              } px-4 py-1 font-bold rounded`}
              onClick={() => setCurTemplate('1')}
            >
              Template 1
            </button>
            <button
              className={`${
                curTemplate === '2'
                  ? 'bg-neutral-700 text-white'
                  : 'border border-neutral-300 text-neutral-700'
              } px-4 py-1 font-bold rounded`}
              onClick={() => setCurTemplate('2')}
            >
              Template 2
            </button>
          </div>
          {curTemplate === '1' && <Template1 resume={form} />}
          {curTemplate === '2' && <Template2 resume={form} />}
        </div>
      </section>
    </Modal>
  );
}

export default ResumeModal;
