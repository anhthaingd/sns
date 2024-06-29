import Modal from '@/modal';
import React, {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { IoCloudUploadOutline } from 'react-icons/io5';
import ReactQuill from 'react-quill';
import { FaXmark } from 'react-icons/fa6';
import { ModalContext } from '../../context/ModalProvider';
import useClickOutside from '../../hooks/useClickOutside';
import { useUpdatePostMutation } from '../../services/redux/query/usersQuery';
import { FetchDataContext } from '../../context/FetchDataProvider';
function UpdatePostModal() {
  const { user } = useContext(FetchDataContext);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [modalRef, clickOutside] = useClickOutside();
  const imgRef = useRef();
  const [form, setForm] = useState({
    postId: '',
    channelId: '',
    content: '',
    oldImages: null,
    images: null,
  });
  const [
    updatePost,
    {
      data: updateData,
      isSuccess: isSuccessUpdate,
      isLoading: isLoadingUpdate,
      isError: isErrorUpdate,
      error: errorUpdate,
    },
  ] = useUpdatePostMutation();
  useEffect(() => {
    if (state.visibleUpdatePostModal) {
      setForm({
        postId: state.visibleUpdatePostModal?._id,
        channelId: state.visibleUpdatePostModal?.channel?._id,
        content: state.visibleUpdatePostModal?.content,
        oldImages: state.visibleUpdatePostModal?.images,
        images: null,
      });
    } else {
      setForm({
        postId: '',
        channelId: '',
        content: '',
        oldImages: null,
        images: null,
      });
    }
  }, [state.visibleUpdatePostModal]);
  const handleUploadImg = () => {
    if (imgRef?.current) {
      imgRef.current.click();
    }
  };
  const handleFileSelected = (e) => {
    const file = e.target.files?.[0];
    setForm({ ...form, images: file });
  };
  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const data = new FormData();
      data.append('content', form.content);
      data.append('oldImages', JSON.stringify(form.oldImages));
      form.images && data.append('images', form.images);
      await updatePost({
        channelId: form?.channelId,
        postId: form?.postId,
        body: data,
      });
    },
    [updatePost, form, user]
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
          state.visibleUpdatePostModal ? 'translate-x-0' : 'translate-x-[100%]'
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
            <h1 className='text-xl sm:text-2xl font-bold'>Update Post</h1>
            <button
              type='button'
              aria-label='close-modal'
              onClick={() => setVisibleModal('visibleUpdatePostModal')}
            >
              <FaXmark className='text-2xl sm:text-3xl' />
            </button>
          </div>
          <div className='h-full flex flex-col gap-6 p-4 overflow-y-auto'>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='images'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Images
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
                    name='images'
                    ref={imgRef}
                    accept='image/*,.jpeg,.jpg,.png,.webp'
                    type='file'
                    style={{ display: 'none' }}
                    onChange={handleFileSelected}
                  />
                </div>
                {/* {!form?.avatar && form.oldAvatar && (
                  <div className='relative w-[96px] h-[96px]'>
                    <img
                      className='w-full h-full object-cover'
                      src={`${import.meta.env.VITE_BACKEND_URL}/${
                        form?.oldAvatar?.url
                      }`}
                      alt={form?.oldAvatar?.name}
                      {...{ fetchPriority: 'low' }}
                    />
                  </div>
                )} */}
                <div className='flex flex-wrap gap-4'>
                  {form?.oldImages && !form.images && (
                    <div className='relative w-[96px] h-[96px]'>
                      <img
                        className='w-full h-full object-cover'
                        src={`${import.meta.env.VITE_BACKEND_URL}/${
                          form?.oldImages?.url
                        }`}
                        alt={form?.oldImages?.name}
                        {...{ fetchPriority: 'low' }}
                      />
                    </div>
                  )}
                  {form.images !== null && (
                    <div className='relative w-[96px] h-[96px]'>
                      <img
                        className='w-full h-full object-cover'
                        src={URL.createObjectURL(form.images)}
                        alt={form.images?.name}
                        {...{ fetchPriority: 'low' }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='content'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Content
              </label>
              <div className='col-span-8 sm:col-span-4'>
                <ReactQuill
                  className='dark:text-neutral-300 h-full p-4 border border-neutral-300 rounded-lg'
                  modules={{ toolbar: false }}
                  placeholder={`What's on your mind, ${
                    user?.username?.split(' ')[
                      user?.username?.split(' ').length - 1
                    ]
                  }?`}
                  value={form.content}
                  onChange={(value) => setForm({ ...form, content: value })}
                />
              </div>
            </div>
            <div className='mt-auto flex justify-end items-stretch gap-4 font-bold'>
              <button
                type='button'
                className='border border-neutral-700 rounded px-4 py-2 hover:border-red-300 hover:text-red-400 transition-colors'
                onClick={() => setVisibleModal('visibleUpdatePostModal')}
              >
                Cancel
              </button>
              <button
                type='submit'
                className='bg-neutral-700 text-white rounded px-4 py-2 hover:bg-blue-500 transition-colors'
              >
                Update Post
              </button>
            </div>
          </div>
        </form>
      </section>
    </Modal>
  );
}

export default UpdatePostModal;
