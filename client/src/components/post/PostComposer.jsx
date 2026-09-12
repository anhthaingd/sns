import { useCallback, useContext, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { FaImage, FaXmark, FaPaperPlane } from 'react-icons/fa6';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { useCreatePostMutation } from '../../services/redux/query/api/postsApi';
import useMutationToast from '../../hooks/useMutationToast';
import Avatar from '../ui/Avatar';
import Button from '../ui/Button';
import Card from '../ui/Card';
import IconButton from '../ui/IconButton';
import Select from '../ui/Select';

/**
 * Ô soạn bài.
 *
 * Dùng chung cho bảng tin và trang channel. Trước đây là HAI file gần như
 * giống hệt nhau (`Home/components/CreatePost` và
 * `Channels/ChanelDetails/components/CreatePost`), nên mọi sửa đổi đều phải
 * làm hai lần — và trên thực tế chỉ được làm một.
 *
 * @param channelId có giá trị thì bài luôn đăng vào channel đó và ô chọn
 *                  channel biến mất.
 *
 * Mặc định thu gọn thành một dòng. Bản cũ luôn mở hết cỡ: ô chọn channel,
 * trình soạn thảo, khung "thêm vào bài viết" và nút đăng chiếm gần trọn màn
 * hình đầu tiên, nên bài viết mới nhất bị đẩy xuống dưới nếp gấp — trên một
 * trang mà việc chính là ĐỌC bảng tin.
 */
function PostComposer({ channelId }) {
  const { t } = useTranslation(['post', 'channel', 'common']);
  const { user, channels } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const imgRef = useRef();
  const [expanded, setExpanded] = useState(false);
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
  const [form, setForm] = useState({ channel: channelId || '', content: '', images: null });

  const handleFileSelected = (e) => {
    const file = e.target.files[0];
    if (file) setForm((prev) => ({ ...prev, images: file }));
    // Chọn lại đúng file vừa gỡ cũng phải kích hoạt onChange, nên xoá value.
    e.target.value = '';
  };

  const handleSubmit = useCallback(async () => {
    if (!form.channel || !form.content) return;
    const formData = new FormData();
    if (form.images) formData.append('images', form.images);
    formData.append('content', form.content);
    await createPost({ channelId: form.channel, body: formData });
  }, [createPost, form]);

  useMutationToast(
    { data: createData, error: errorCreate, isSuccess: isSuccessCreate, isError: isErrorCreate },
    {
      onSuccess: () => {
        setForm({ channel: channelId || '', content: '', images: null });
        setExpanded(false);
      },
    }
  );

  const firstName = user?.username?.split(' ').slice(-1)[0];
  // Quill trả về "<p><br></p>" cho ô rỗng, không phải chuỗi rỗng.
  const hasContent = Boolean(form.content?.replace(/<[^>]*>/g, '').trim());

  if (!expanded) {
    return (
      <Card padded={false} className='p-3'>
        <div className='flex items-center gap-3'>
          <Avatar src={user?.avatar} name={user?.username} size='md' />
          <button
            type='button'
            data-testid='composer-open'
            className='h-10 flex-1 rounded-pill bg-surface-2 px-4 text-left text-sm text-fg-subtle transition-colors hover:bg-surface-3'
            onClick={() => setExpanded(true)}
          >
            {t('create.placeholder', { name: firstName })}
          </button>
          <IconButton
            variant='soft'
            label={t('create.addImage')}
            onClick={() => setExpanded(true)}
          >
            <FaImage className='size-4 text-accent-text' />
          </IconButton>
        </div>
      </Card>
    );
  }

  return (
    <Card className='animate-rise' aria-busy={isLoadingCreate}>
      <div className='flex items-center gap-3'>
        <Avatar src={user?.avatar} name={user?.username} size='md' />
        <div className='min-w-0 flex-1'>
          <button
            type='button'
            className='block truncate text-sm font-bold text-fg hover:text-accent-text'
            onClick={() => navigate(`/profile/${user?._id}`)}
          >
            {user?.username}
          </button>
          <p className='text-xs capitalize text-fg-subtle'>{user?.role?.name}</p>
        </div>
        <IconButton
          size='sm'
          label={t('common:actions.close')}
          onClick={() => setExpanded(false)}
        >
          <FaXmark className='size-4' />
        </IconButton>
      </div>

      <div className='mt-4 flex flex-col gap-3'>
        {/* Trong trang channel thì channel đã biết trước — hỏi lại là thừa,
            và tệ hơn: người dùng có thể chọn nhầm sang channel khác rồi tưởng
            mình vừa đăng vào channel đang mở. */}
        {!channelId && (
          <Select
            aria-label={t('channel:title')}
            value={form.channel}
            onChange={(e) => setForm({ ...form, channel: e.target.value })}
          >
            <option value=''>{t('create.selectChannel')}</option>
            {channels?.map((c) => (
              <option key={c._id} value={c._id}>
                {c.name}
              </option>
            ))}
          </Select>
        )}

        <ReactQuill
          modules={{ toolbar: false }}
          placeholder={t('create.placeholder', { name: firstName })}
          value={form.content}
          onChange={(value) => setForm({ ...form, content: value })}
        />

        {form.images && (
          <div className='relative overflow-hidden rounded-lg ring-1 ring-inset ring-line'>
            <img
              className='max-h-72 w-full object-cover'
              src={URL.createObjectURL(form.images)}
              alt={t('create.imageAlt', { index: 1 })}
            />
            <IconButton
              size='sm'
              label={t('create.removeImage')}
              className='absolute right-2 top-2 bg-ai-950/60 text-white hover:bg-ai-950/80 hover:text-white'
              onClick={() => setForm({ ...form, images: null })}
            >
              <FaXmark className='size-3.5' />
            </IconButton>
          </div>
        )}

        <div className='flex items-center justify-between gap-3 border-t border-line pt-3'>
          <Button
            variant='ghost'
            size='sm'
            icon={FaImage}
            onClick={() => imgRef.current?.click()}
          >
            {t('create.addImage')}
          </Button>
          <input
            ref={imgRef}
            className='hidden'
            accept='image/jpeg,image/png,image/webp'
            type='file'
            onChange={handleFileSelected}
          />
          <Button
            icon={FaPaperPlane}
            loading={isLoadingCreate}
            disabled={!form.channel || !hasContent}
            onClick={handleSubmit}
          >
            {t('create.submit')}
          </Button>
        </div>
      </div>
    </Card>
  );
}

export default PostComposer;
