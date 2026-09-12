import { useCallback, useContext, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ModalContext } from '../../context/ModalProvider';
import { useCreateChannelMutation } from '../../services/redux/query/api/channelsApi';
import useMutationToast from '../../hooks/useMutationToast';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Input from '../ui/Input';
import Textarea from '../ui/Textarea';
import ImageUpload from '../ui/ImageUpload';

const EMPTY = { name: '', intro: '', background: null };

function AddChannelModal() {
  const { t } = useTranslation(['channel', 'common']);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [form, setForm] = useState(EMPTY);
  const [
    createChannel,
    {
      data: postData,
      isSuccess: isSuccessPost,
      isLoading: isLoadingPost,
      isError: isErrorPost,
      error: errorPost,
    },
  ] = useCreateChannelMutation();

  const close = useCallback(
    () => setVisibleModal('visibleAddChannelModal'),
    [setVisibleModal]
  );

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const data = new FormData();
      data.append('name', form.name);
      data.append('intro', form.intro);
      if (form.background) data.append('images', form.background);
      await createChannel(data);
    },
    [createChannel, form]
  );

  useMutationToast(
    { data: postData, error: errorPost, isSuccess: isSuccessPost, isError: isErrorPost },
    {
      onSuccess: () => {
        setForm(EMPTY);
        close();
      },
    }
  );

  return (
    <Dialog
      open={Boolean(state.visibleAddChannelModal)}
      onClose={close}
      title={t('add.title')}
      busy={isLoadingPost}
      footer={
        <>
          <Button variant='outline' onClick={close} disabled={isLoadingPost}>
            {t('common:actions.cancel')}
          </Button>
          <Button form='fu-add-channel' type='submit' loading={isLoadingPost}>
            {t('common:actions.add')}
          </Button>
        </>
      }
    >
      <form id='fu-add-channel' className='flex flex-col gap-4' onSubmit={handleSubmit}>
        <Field label={t('field.background')}>
          <ImageUpload
            value={form.background}
            onChange={(file) => setForm((prev) => ({ ...prev, background: file }))}
            onRemove={() => setForm((prev) => ({ ...prev, background: null }))}
          />
        </Field>

        <Field label={t('field.name')} required>
          {(aria) => (
            <Input
              {...aria}
              required
              placeholder={t('add.namePlaceholder')}
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            />
          )}
        </Field>

        <Field label={t('field.intro')}>
          {(aria) => (
            <Textarea
              {...aria}
              rows={3}
              placeholder={t('add.introPlaceholder')}
              value={form.intro}
              onChange={(e) => setForm((prev) => ({ ...prev, intro: e.target.value }))}
            />
          )}
        </Field>
      </form>
    </Dialog>
  );
}

export default AddChannelModal;
