import { useCallback, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ReactQuill from 'react-quill';
import { ModalContext } from '../../context/ModalProvider';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { useUpdatePostMutation } from '../../services/redux/query/api/postsApi';
import useMutationToast from '../../hooks/useMutationToast';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import ImageUpload from '../ui/ImageUpload';

const EMPTY = { postId: '', channelId: '', content: '', oldImages: null, images: null };

function UpdatePostModal() {
  const { t } = useTranslation(['post', 'common']);
  const { user } = useContext(FetchDataContext);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [form, setForm] = useState(EMPTY);
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

  const open = Boolean(state.visibleUpdatePostModal);
  const close = useCallback(
    () => setVisibleModal('visibleUpdatePostModal'),
    [setVisibleModal]
  );

  useEffect(() => {
    const post = state.visibleUpdatePostModal;
    setForm(
      post
        ? {
            postId: post?._id,
            channelId: post?.channel?._id,
            content: post?.content,
            oldImages: post?.images,
            images: null,
          }
        : EMPTY
    );
  }, [state.visibleUpdatePostModal]);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const data = new FormData();
      data.append('content', form.content);
      data.append('oldImages', JSON.stringify(form.oldImages));
      if (form.images) data.append('images', form.images);
      await updatePost({
        channelId: form?.channelId,
        postId: form?.postId,
        body: data,
      });
    },
    [updatePost, form]
  );

  useMutationToast(
    {
      data: updateData,
      error: errorUpdate,
      isSuccess: isSuccessUpdate,
      isError: isErrorUpdate,
    },
    { onSuccess: close }
  );

  const firstName = user?.username?.split(' ').slice(-1)[0];

  return (
    // Bản cũ là một tấm bảng trượt ra chiếm nửa màn hình, đặt ô nhập theo lưới
    // 6 cột với nhãn ở cột trái — sửa một bài viết ngắn mà mở ra như một trang
    // cấu hình. Hộp thoại vừa nội dung sát với việc đang làm hơn.
    <Dialog
      open={open}
      onClose={close}
      title={t('update.title')}
      size='lg'
      busy={isLoadingUpdate}
      footer={
        <>
          <Button variant='outline' onClick={close} disabled={isLoadingUpdate}>
            {t('common:actions.cancel')}
          </Button>
          <Button form='fu-update-post' type='submit' loading={isLoadingUpdate}>
            {t('common:actions.save')}
          </Button>
        </>
      }
    >
      <form id='fu-update-post' className='flex flex-col gap-4' onSubmit={handleSubmit}>
        <Field label={t('update.content')}>
          <ReactQuill
            modules={{ toolbar: false }}
            placeholder={t('create.placeholder', { name: firstName })}
            value={form.content}
            onChange={(value) => setForm((prev) => ({ ...prev, content: value }))}
          />
        </Field>

        <Field label={t('update.images')}>
          <ImageUpload
            value={form.images}
            existing={form.oldImages}
            onChange={(file) => setForm((prev) => ({ ...prev, images: file }))}
            onRemove={() => setForm((prev) => ({ ...prev, images: null }))}
          />
        </Field>
      </form>
    </Dialog>
  );
}

export default UpdatePostModal;
