import React, {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { useNavigate } from 'react-router-dom';
import { useCreatePostMutation } from '../../../../../services/redux/query/usersQuery';
import { FetchDataContext } from '../../../../../context/FetchDataProvider';
import { ModalContext } from '../../../../../context/ModalProvider';
import { icons } from '../../../../../assets/icons';

function CreatePost({ channelId }) {
  const { user } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const { setVisibleModal } = useContext(ModalContext);
  const imgRef = useRef();
  const [
    createPost,
    {
      data: createData,
      isSuccess: isSuccessCreate,
      isLoading: isLoadingCreate,
      isError: isErrorCreate,
      error: errorCreate,
    },
  ] = useCreatePostMutation();
  const [form, setForm] = useState({
    channel: channelId,
    content: '',
    images: null,
  });
  const handleUploadImg = () => {
    if (imgRef?.current) {
      imgRef.current.click();
    }
  };
  const handleFileSelected = (e) => {
    const file = e.target.files[0];
    setForm({ ...form, images: file });
  };
  const handleSubmit = useCallback(async () => {
    if (form.channel && form.content) {
      const formData = new FormData();
      formData.append('images', form.images);
      formData.append('content', form.content);
      await createPost({ channelId: form.channel, body: formData });
    }
  }, [createPost, form]);
  useEffect(() => {
    if (isSuccessCreate && createData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: createData?.message,
        },
      });
      setForm({ channel: channelId, content: '', images: null });
    }
    if (isErrorCreate && errorCreate) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorCreate?.data?.message,
        },
      });
    }
  }, [isSuccessCreate, createData, isErrorCreate, errorCreate]);
  return (
    <div
      className='rounded-md bg-neutral-100 dark:bg-neutral-800'
      aria-disabled={isLoadingCreate}
    >
      <div className='p-4 flex flex-col gap-8'>
        <div className='flex items-center gap-4'>
          <div className='size-[40px] rounded-full overflow-hidden'>
            <img
              className='w-full h-full object-cover'
              src={`${import.meta.env.VITE_BACKEND_URL}/${user?.avatar?.url}`}
              alt={user?.username}
            />
          </div>
          <div className='flex flex-col gap-2'>
            <h2
              className='font-bold text-base md:text-lg cursor-pointer'
              onClick={() => navigate(`/profile/${user?._id}`)}
            >
              {user?.username}
            </h2>
            <p className='capitalize px-4 py-1 border border-neutral-300 flex justify-center items-center rounded-lg text-sm bg-neutral-200 dark:bg-neutral-600'>
              {user?.role?.name}
            </p>
          </div>
        </div>
        <div className='rounded-lg overflow-hidden border border-neutral-300 h-[10vh]'>
          <ReactQuill
            className='dark:text-neutral-300 h-full'
            modules={{ toolbar: false }}
            placeholder={`What's on your mind, ${
              user?.username?.split(' ')[user?.username?.split(' ').length - 1]
            }?`}
            value={form.content}
            onChange={(value) => setForm({ ...form, content: value })}
          />
        </div>
        <div className='grid grid-cols-2'>
          {form.images && (
            <img
              src={URL.createObjectURL(form.images)}
              key={form.images.name}
              alt='index'
              {...{ fetchPriority: 'low' }}
            />
          )}
        </div>
        <div className='p-4 border border-neutral-300 rounded-lg flex justify-between items-center'>
          <p className='font-medium'>Add to your post</p>
          <div className='flex justify-center items-center'>
            <button
              dangerouslySetInnerHTML={{ __html: icons.image_icon }}
              aria-label='img-btn'
              onClick={handleUploadImg}
            ></button>
            <input
              ref={imgRef}
              accept='image/*,.jpeg,.jpg,.png,.webp'
              type='file'
              style={{ display: 'none' }}
              onChange={handleFileSelected}
            />
          </div>
        </div>
        <button
          className='py-4 text-base md:text-lg font-bold bg-neutral-700 dark:bg-neutral-300 text-white dark:text-neutral-700 rounded-lg'
          disabled={!form.channel || !form.content || isLoadingCreate}
          onClick={handleSubmit}
        >
          Post
        </button>
      </div>
    </div>
  );
}

export default CreatePost;
