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
import { useUpdateUserMutation } from '../../services/redux/query/usersQuery';
import { FetchDataContext } from '../../context/FetchDataProvider';
function UpdateProfileModal() {
  const { user } = useContext(FetchDataContext);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [modalRef, clickOutside] = useClickOutside();
  const avatarRef = useRef();
  const coverBgRef = useRef();
  const [form, setForm] = useState({
    username: '',
    address: '',
    intro: '',
    oldPassword: '',
    newPassword: '',
    avatar: null,
    oldAvatar: null,
    cover_bg: null,
    oldCoverBg: null,
  });
  const [
    updateUser,
    {
      data: updateData,
      isSuccess: isSuccessUpdate,
      isLoading: isLoadingUpdate,
      isError: isErrorUpdate,
      error: errorUpdate,
    },
  ] = useUpdateUserMutation();
  useEffect(() => {
    if (user) {
      setForm({
        username: user?.username,
        address: user?.address,
        intro: user?.intro,
        oldPassword: user?.password,
        newPassword: user?.password,
        avatar: null,
        oldAvatar: user?.avatar,
        cover_bg: null,
        oldCoverBg: user?.cover_bg,
      });
    } else {
      setForm({
        username: '',
        address: '',
        intro: '',
        oldPassword: '',
        newPassword: '',
        avatar: null,
        oldAvatar: null,
        cover_bg: null,
        oldCoverBg: null,
      });
    }
  }, [user]);
  const handleUploadImg = (name) => {
    if (name === 'avatar' && avatarRef?.current) {
      avatarRef.current.click();
    }
    if (name === 'cover' && coverBgRef?.current) {
      coverBgRef.current.click();
    }
  };
  const handleFileSelected = (e) => {
    const { name } = e.target;
    const file = e.target.files?.[0];
    setForm({ ...form, [name]: file });
  };
  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const data = new FormData();
      data.append('username', form.username);
      data.append('address', form.address);
      data.append('intro', form.intro);
      data.append('oldPassword', form.oldPassword);
      data.append('newPassword', form.newPassword);
      data.append('oldAvatar', JSON.stringify(form.oldAvatar));
      data.append('oldCoverBg', JSON.stringify(form.oldCoverBg));
      if (form.cover_bg && form.avatar) {
        data.append('update_images', 'both');
      }
      if (form.cover_bg && !form.avatar) {
        data.append('update_images', 'cover_bg');
      }
      if (form.avatar && !form.cover_bg) {
        data.append('update_images', 'avatar');
      }
      form.avatar && data.append('images', form.avatar);
      form.cover_bg && data.append('images', form.cover_bg);
      await updateUser({ id: user._id, body: data });
    },
    [updateUser, form, user]
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
          state.visibleUpdateProfileModal
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
            <h1 className='text-xl sm:text-2xl font-bold'>Update Profile</h1>
            <button
              type='button'
              aria-label='close-modal'
              onClick={() => setVisibleModal('visibleUpdateProfileModal')}
            >
              <FaXmark className='text-2xl sm:text-3xl' />
            </button>
          </div>
          <div className='h-full flex flex-col gap-6 p-4 overflow-y-auto'>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='avatar'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Avatar
              </label>
              <div className='col-span-8 sm:col-span-4 flex flex-col gap-4'>
                <div className='border-2 border-dotted border-neutral-300 rounded-lg'>
                  <div
                    className='w-full h-full p-4 cursor-pointer flex flex-col items-center gap-2'
                    role='presentation'
                    onClick={() => handleUploadImg('avatar')}
                  >
                    <IoCloudUploadOutline className='text-2xl text-blue-500' />
                    <p className='font-bold'>Upload your image here</p>
                    <p className='italic text-sm'>
                      (Only *.jpeg, *.webp and *.png images will be accepted)
                    </p>
                  </div>
                  <input
                    name='avatar'
                    ref={avatarRef}
                    accept='image/*,.jpeg,.jpg,.png,.webp'
                    type='file'
                    style={{ display: 'none' }}
                    onChange={handleFileSelected}
                  />
                </div>
                {!form?.avatar && form.oldAvatar && (
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
                )}
                {form?.avatar && (
                  <div className='relative w-[96px] h-[96px]'>
                    <img
                      className='w-full h-full object-cover'
                      src={URL.createObjectURL(form.avatar)}
                      alt={form.avatar.name}
                      {...{ fetchPriority: 'low' }}
                    />
                    <button
                      className='absolute top-1 right-1 border border-red-500 text-red-500 rounded-full p-1'
                      aria-label='remove-img'
                      type='button'
                      onClick={() =>
                        setForm({
                          ...form,
                          avatar: null,
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
                htmlFor='cover_bg'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Cover Background
              </label>
              <div className='col-span-8 sm:col-span-4 flex flex-col gap-4'>
                <div className='border-2 border-dotted border-neutral-300 rounded-lg'>
                  <div
                    className='w-full h-full p-4 cursor-pointer flex flex-col items-center gap-2'
                    role='presentation'
                    onClick={() => handleUploadImg('cover')}
                  >
                    <IoCloudUploadOutline className='text-2xl text-blue-500' />
                    <p className='font-bold'>Upload your image here</p>
                    <p className='italic text-sm'>
                      (Only *.jpeg, *.webp and *.png images will be accepted)
                    </p>
                  </div>
                  <input
                    name='cover_bg'
                    ref={coverBgRef}
                    accept='image/*,.jpeg,.jpg,.png,.webp'
                    type='file'
                    style={{ display: 'none' }}
                    onChange={handleFileSelected}
                  />
                </div>
                {form?.oldCoverBg &&
                  form?.oldCoverBg?.url &&
                  !form.cover_bg && (
                    <div className='relative w-[96px] h-[96px]'>
                      <img
                        className='w-full h-full object-cover'
                        src={`${import.meta.env.VITE_BACKEND_URL}/${
                          form?.oldCoverBg?.url
                        }`}
                        alt={form?.oldCoverBg?.name}
                        {...{ fetchPriority: 'low' }}
                      />
                    </div>
                  )}
                {form?.cover_bg && (
                  <div className='relative w-[96px] h-[96px]'>
                    <img
                      className='w-full h-full object-cover'
                      src={URL.createObjectURL(form.cover_bg)}
                      alt={form.cover_bg.name}
                      {...{ fetchPriority: 'low' }}
                    />
                    <button
                      className='absolute top-1 right-1 border border-red-500 text-red-500 rounded-full p-1'
                      aria-label='remove-img'
                      type='button'
                      onClick={() =>
                        setForm({
                          ...form,
                          cover_bg: null,
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
                htmlFor='username'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Username
              </label>
              <div className='col-span-8 sm:col-span-4'>
                <input
                  id='username'
                  name='username'
                  className='block w-full h-12 border px-3 py-1 text-sm leading-5 rounded-md bg-gray-100 dark:bg-neutral-800 focus:border-gray-200 border-gray-200'
                  type='text'
                  placeholder='Enter your new username...'
                  value={form.username}
                  onChange={(e) =>
                    setForm({ ...form, username: e.target.value })
                  }
                />
              </div>
            </div>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='password'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Password
              </label>
              <div className='col-span-8 sm:col-span-4'>
                <input
                  id='password'
                  name='password'
                  className='block w-full h-12 border px-3 py-1 text-sm leading-5 rounded-md bg-gray-100 dark:bg-neutral-800 focus:border-gray-200 border-gray-200'
                  type='password'
                  placeholder='Enter your new password...'
                  value={form.newPassword}
                  onChange={(e) =>
                    setForm({ ...form, newPassword: e.target.value })
                  }
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
                  name='intro'
                  className='block w-full h-12 border px-3 py-2 text-sm leading-5 rounded-md bg-gray-100 dark:bg-neutral-800 focus:border-gray-200 border-gray-200 focus:outline-none'
                  placeholder='Enter your new intro...'
                  rows={10}
                  value={form.intro}
                  onChange={(e) => setForm({ ...form, intro: e.target.value })}
                />
              </div>
            </div>
            <div className='grid grid-cols-6 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
              <label
                htmlFor='address'
                className='block text-sm col-span-4 sm:col-span-2 font-medium'
              >
                Address
              </label>
              <div className='col-span-8 sm:col-span-4'>
                <input
                  id='address'
                  name='address'
                  className='block w-full h-12 border px-3 py-1 text-sm leading-5 rounded-md bg-gray-100 dark:bg-neutral-800 focus:border-gray-200 border-gray-200'
                  type='address'
                  placeholder='Enter your new address...'
                  value={form.address}
                  onChange={(e) =>
                    setForm({ ...form, address: e.target.value })
                  }
                />
              </div>
            </div>
            <div className='mt-auto flex justify-end items-stretch gap-4 font-bold'>
              <button
                type='button'
                className='border border-neutral-700 rounded px-4 py-2 hover:border-red-300 hover:text-red-400 transition-colors'
                onClick={() => setVisibleModal('visibleUpdateProfileModal')}
              >
                Cancel
              </button>
              <button
                type='submit'
                className='bg-neutral-700 text-white rounded px-4 py-2 hover:bg-blue-500 transition-colors'
              >
                Update Profile
              </button>
            </div>
          </div>
        </form>
      </section>
    </Modal>
  );
}

export default UpdateProfileModal;
