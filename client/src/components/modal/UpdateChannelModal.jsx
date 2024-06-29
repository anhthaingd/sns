import Modal from '@/modal';
import React, {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { IoCloudUploadOutline } from 'react-icons/io5';
import { FaXmark } from 'react-icons/fa6';
import { ModalContext } from '../../context/ModalProvider';
import useClickOutside from '../../hooks/useClickOutside';
import { useUpdateChannelMutation } from '../../services/redux/query/usersQuery';
function UpdateChannelModal() {
  const { state, setVisibleModal } = useContext(ModalContext);
  const [modalRef, clickOutside] = useClickOutside();
  const imgRef = useRef();
  const [form, setForm] = useState({
    name: '',
    intro: '',
    background: null,
    oldBackground: null,
  });
  const [
    updateChannel,
    {
      data: updateData,
      isSuccess: isSuccessUpdate,
      isLoading: isLoadingUpdate,
      isError: isErrorUpdate,
      error: errorUpdate,
    },
  ] = useUpdateChannelMutation();
  useEffect(() => {
    if (state.visibleUpdateChannelModal) {
      setForm({
        name: state.visibleUpdateChannelModal?.name,
        intro: state.visibleUpdateChannelModal?.intro,
        background: null,
        oldBackground: state.visibleUpdateChannelModal?.background,
      });
    } else {
      setForm({
        name: '',
        intro: '',
        background: null,
        oldBackground: null,
      });
    }
  }, [state.visibleUpdateChannelModal]);
  const handleUploadImg = () => {
    if (imgRef?.current) {
      imgRef.current.click();
    }
  };
  const handleFileSelected = (e) => {
    const file = e.target.files?.[0];
    setForm({ ...form, background: file });
  };
  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const data = new FormData();
      data.append('name', form.name);
      data.append('intro', form.intro);
      data.append('oldBackground', JSON.stringify(form.oldBackground));
      form.background && data.append('images', form.background);
      await updateChannel({
        id: state.visibleUpdateChannelModal?._id,
        body: data,
      });
    },
    [updateChannel, form, state.visibleUpdateChannelModal]
  );
  useEffect(() => {
    if (isSuccessUpdate && updateData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: updateData?.message,
        },
      });
    }
    if (isErrorUpdate && errorUpdate) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorUpdate?.data?.message,
        },
      });
    }
  }, [
    isSuccessUpdate,
    updateData,
    isErrorUpdate,
    errorUpdate,
    setVisibleModal,
  ]);
  return (
    <Modal>
      <section
        style={{ backgroundColor: 'rgba(51,51,51,0.9)' }}
        className={`fixed right-0 top-0 w-full h-full z-[100] flex justify-end overflow-hidden transition-all duration-200 ${
          state.visibleUpdateChannelModal
            ? 'translate-x-0'
            : 'translate-x-[100%]'
        } `}
        onClick={clickOutside}
        aria-disabled={isLoadingUpdate}
      >
        <form
          className='w-full lg:w-1/2 h-full bg-slate-50 dark:bg-neutral-800 dark:text-neutral-100 flex flex-col gap-12'
          ref={modalRef}
          onSubmit={handleSubmit}
        >
          <div className='px-4 py-4 sm:py-6 flex justify-between items-center gap-4 bg-neutral-200 dark:bg-neutral-700 dark:text-neutral-100'>
            <h1 className='text-xl sm:text-2xl font-bold'>Update Channel</h1>
            <button
              type='button'
              aria-label='close-modal'
              onClick={() => setVisibleModal('visibleUpdateChannelModal')}
            >
              <FaXmark className='text-2xl sm:text-3xl' />
            </button>
          </div>
          <div className='h-full flex flex-col gap-6 p-4 overflow-y-auto'>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='background'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Background
              </label>
              <div className='col-span-8 sm:col-span-4 flex flex-col gap-4'>
                <div className='border-2 border-dotted border-neutral-300 rounded-lg'>
                  <div
                    className='w-full h-full p-4 cursor-pointer flex flex-col items-center gap-2'
                    role='presentation'
                    onClick={handleUploadImg}
                  >
                    <IoCloudUploadOutline className='text-2xl text-blue-500' />
                    <p className='font-bold'>Upload your image here</p>
                    <p className='italic text-sm'>
                      (Only *.jpeg, *.webp and *.png images will be accepted)
                    </p>
                  </div>
                  <input
                    ref={imgRef}
                    accept='image/*,.jpeg,.jpg,.png,.webp'
                    type='file'
                    style={{ display: 'none' }}
                    onChange={handleFileSelected}
                  />
                </div>
                {form?.oldBackground && !form?.background && (
                  <div className='relative w-[96px] h-[96px]'>
                    <img
                      className='w-full h-full object-cover'
                      src={`${import.meta.env.VITE_BACKEND_URL}/${
                        form?.oldBackground?.url
                      }`}
                      alt={form?.oldBackground?.name}
                      {...{ fetchPriority: 'low' }}
                    />
                  </div>
                )}
                {form?.background && (
                  <div className='relative w-[96px] h-[96px]'>
                    <img
                      className='w-full h-full object-cover'
                      src={URL.createObjectURL(form.background)}
                      alt={form.background.name}
                      {...{ fetchPriority: 'low' }}
                    />
                    <button
                      className='absolute top-1 right-1 border border-red-500 text-red-500 rounded-full p-1'
                      aria-label='remove-img'
                      type='button'
                      onClick={() =>
                        setForm({
                          ...form,
                          background: null,
                        })
                      }
                    >
                      <FaXmark />
                    </button>
                  </div>
                )}
              </div>
            </div>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='name'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Name
              </label>
              <div className='col-span-8 sm:col-span-4'>
                <input
                  id='name'
                  name='name'
                  className='block w-full h-12 border px-3 py-1 text-sm leading-5 rounded-md bg-gray-100 dark:bg-neutral-800 focus:border-gray-200 border-gray-200'
                  type='text'
                  placeholder='Enter Channel name...'
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
            </div>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='intro'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Intro
              </label>
              <div className='col-span-8 sm:col-span-4'>
                <textarea
                  id='intro'
                  name='name'
                  className='block w-full h-12 border p-3 text-sm leading-5 rounded-md bg-gray-100 dark:bg-neutral-800 focus:border-gray-200 border-gray-200'
                  placeholder='Enter channel intro...'
                  value={form.intro}
                  onChange={(e) => setForm({ ...form, intro: e.target.value })}
                  rows={5}
                />
              </div>
            </div>
            <div className='mt-auto flex justify-end items-stretch gap-4 font-bold'>
              <button
                type='button'
                className='border border-neutral-700 rounded px-4 py-2 hover:border-red-300 hover:text-red-400 transition-colors'
                onClick={() => setVisibleModal('visibleUpdateChannelModal')}
              >
                Cancel
              </button>
              <button
                type='submit'
                className='bg-neutral-700 text-white rounded px-4 py-2 hover:bg-blue-500 transition-colors'
              >
                Update Channel
              </button>
            </div>
          </div>
        </form>
      </section>
    </Modal>
  );
}

export default UpdateChannelModal;
