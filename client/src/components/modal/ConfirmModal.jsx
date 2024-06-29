import React, { useContext } from 'react';
import { ModalContext } from '../../context/ModalProvider';
import useClickOutside from '../../hooks/useClickOutside';

function ConfirmModal() {
  const { state, setVisibleModal } = useContext(ModalContext);
  const [modalRef, clickOutside] = useClickOutside();
  return (
    <section
      style={{ backgroundColor: 'rgba(51,51,51,0.9)' }}
      className={`fixed right-0 top-0 w-full h-full z-[100] justify-center items-center overflow-hidden transition-all duration-200 ${
        state.visibleConfirmModal ? 'flex' : 'hidden'
      } `}
      onClick={clickOutside}
      disabled={state.visibleConfirmModal?.loading}
    >
      <div
        className='bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 border border-neutral-300 dark:border-neutral-600 w-[576px] h-[282px] py-4 px-6 rounded-lg flex flex-col gap-[26px]'
        ref={modalRef}
        disabled={state.visibleConfirmModal?.loading}
      >
        <div className='px-8 pt-6 pb-4 flex flex-col items-center gap-[20px]'>
          <div className='text-3xl'>{state.visibleConfirmModal?.icon}</div>
          <div className='w-full text-center flex flex-col gap-[12px]'>
            <p className='text-lg font-medium'>
              {state.visibleConfirmModal?.question}
            </p>
            <p className='text-sm'>{state.visibleConfirmModal?.description}</p>
          </div>
        </div>
        <div className='flex justify-center items-center gap-[24px] text-sm'>
          <button
            type='button'
            style={{ transition: 'all 0.2s linear' }}
            className='h-[48px] bg-neutral-500 hover:bg-neutral-600 hover:text-white text-gray p-4 flex justify-center items-center rounded-md'
            onClick={() => setVisibleModal('visibleConfirmModal')}
          >
            Cancel
          </button>
          <button
            type='button'
            style={{ transition: 'all 0.2s linear' }}
            className='h-[48px] text-white bg-green-500 hover:bg-green-700 p-4 flex justify-center items-center rounded-md'
            onClick={state.visibleConfirmModal?.acceptFunc}
          >
            Accept
          </button>
        </div>
      </div>
    </section>
  );
}

export default ConfirmModal;
