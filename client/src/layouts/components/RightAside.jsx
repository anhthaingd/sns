import React, { useContext } from 'react';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { ModalContext } from '../../context/ModalProvider';

function RightAside() {
  const { following } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  return (
    <section className='fixed top-0 right-0 mt-[72px] w-[320px] h-[95vh] px-4 font-medium hidden lg:flex flex-col gap-4 overflow-y-auto'>
      <p className='font-bold text-base md:text-lg'>Following</p>
      <div className='pb-4 border-b border-neutral-300 flex flex-col'>
        {following?.map((f) => {
          return (
            <article
              className='flex items-center gap-4 hover:bg-neutral-200 dark:hover:bg-neutral-700 p-2 rounded cursor-pointer'
              key={f?._id}
              onClick={() => setVisibleModal({ visibleChatModal: f })}
            >
              <div className='size-[40px] rounded-full overflow-hidden'>
                <img
                  className='w-full h-full object-cover'
                  src={`${import.meta.env.VITE_BACKEND_URL}/${f?.avatar?.url}`}
                  alt={f?.username}
                  {...{ fetchPriority: 'low' }}
                />
              </div>
              <p>{f?.username}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default RightAside;
