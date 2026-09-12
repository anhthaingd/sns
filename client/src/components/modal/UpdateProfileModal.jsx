import { useCallback, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ModalContext } from '../../context/ModalProvider';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { useUpdateUserMutation } from '../../services/redux/query/api/usersApi';
import useMutationToast from '../../hooks/useMutationToast';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Input from '../ui/Input';
import Textarea from '../ui/Textarea';
import ImageUpload from '../ui/ImageUpload';

const EMPTY = {
  username: '',
  address: '',
  intro: '',
  oldPassword: '',
  newPassword: '',
  avatar: null,
  oldAvatar: null,
  cover_bg: null,
  oldCoverBg: null,
};

function UpdateProfileModal() {
  const { t } = useTranslation(['user', 'common']);
  const { user } = useContext(FetchDataContext);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [form, setForm] = useState(EMPTY);
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

  const close = useCallback(
    () => setVisibleModal('visibleUpdateProfileModal'),
    [setVisibleModal]
  );

  useEffect(() => {
    setForm(
      user
        ? {
            username: user?.username ?? '',
            address: user?.address ?? '',
            intro: user?.intro ?? '',
            oldPassword: user?.password ?? '',
            newPassword: user?.password ?? '',
            avatar: null,
            oldAvatar: user?.avatar,
            cover_bg: null,
            oldCoverBg: user?.cover_bg,
          }
        : EMPTY
    );
  }, [user]);

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
      // Máy chủ nhận cả hai ảnh trong cùng một trường `images`, nên phải nói
      // riêng bằng `update_images` là gói này chứa ảnh nào. Thứ tự append
      // dưới đây (avatar trước, cover sau) là thứ tự máy chủ đọc ra.
      if (form.cover_bg && form.avatar) data.append('update_images', 'both');
      if (form.cover_bg && !form.avatar) data.append('update_images', 'cover_bg');
      if (form.avatar && !form.cover_bg) data.append('update_images', 'avatar');
      if (form.avatar) data.append('images', form.avatar);
      if (form.cover_bg) data.append('images', form.cover_bg);
      await updateUser(data);
    },
    [updateUser, form]
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

  const set = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }));
  const setFile = (key) => (file) => setForm((prev) => ({ ...prev, [key]: file }));

  return (
    <Dialog
      open={Boolean(state.visibleUpdateProfileModal)}
      onClose={close}
      title={t('update.title')}
      size='lg'
      busy={isLoadingUpdate}
      footer={
        <>
          <Button variant='outline' onClick={close} disabled={isLoadingUpdate}>
            {t('common:actions.cancel')}
          </Button>
          <Button form='fu-update-profile' type='submit' loading={isLoadingUpdate}>
            {t('common:actions.save')}
          </Button>
        </>
      }
    >
      <form id='fu-update-profile' className='flex flex-col gap-5' onSubmit={handleSubmit}>
        <div className='grid gap-5 sm:grid-cols-2'>
          <Field label={t('field.avatar')}>
            <ImageUpload
              aspect='aspect-square'
              value={form.avatar}
              existing={form.oldAvatar}
              onChange={setFile('avatar')}
              onRemove={() => setForm((prev) => ({ ...prev, avatar: null }))}
            />
          </Field>
          <Field label={t('field.coverBackground')}>
            <ImageUpload
              value={form.cover_bg}
              existing={form.oldCoverBg}
              onChange={setFile('cover_bg')}
              onRemove={() => setForm((prev) => ({ ...prev, cover_bg: null }))}
            />
          </Field>
        </div>

        <Field label={t('field.username')}>
          {(aria) => (
            <Input
              {...aria}
              placeholder={t('update.usernamePlaceholder')}
              value={form.username}
              onChange={set('username')}
            />
          )}
        </Field>

        <Field label={t('field.password')}>
          {(aria) => (
            <Input
              {...aria}
              type='password'
              autoComplete='new-password'
              placeholder={t('update.passwordPlaceholder')}
              value={form.newPassword}
              onChange={set('newPassword')}
            />
          )}
        </Field>

        <Field label={t('field.intro')}>
          {(aria) => (
            <Textarea
              {...aria}
              rows={3}
              placeholder={t('update.introPlaceholder')}
              value={form.intro}
              onChange={set('intro')}
            />
          )}
        </Field>

        <Field label={t('field.address')}>
          {(aria) => (
            <Input
              {...aria}
              placeholder={t('update.addressPlaceholder')}
              value={form.address}
              onChange={set('address')}
            />
          )}
        </Field>
      </form>
    </Dialog>
  );
}

export default UpdateProfileModal;
