import { useCallback, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ModalContext } from '../../context/ModalProvider';
import { useUpdateChannelMutation } from '../../services/redux/query/api/channelsApi';
import useMutationToast from '../../hooks/useMutationToast';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Input from '../ui/Input';
import Textarea from '../ui/Textarea';
import ImageUpload from '../ui/ImageUpload';

const EMPTY = { name: '', intro: '', background: null, oldBackground: null };

function UpdateChannelModal() {
  const { t } = useTranslation(['channel', 'common']);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [form, setForm] = useState(EMPTY);
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

  const channel = state.visibleUpdateChannelModal;
  const close = useCallback(
    () => setVisibleModal('visibleUpdateChannelModal'),
    [setVisibleModal]
  );

  useEffect(() => {
    setForm(
      channel
        ? {
            name: channel?.name ?? '',
            intro: channel?.intro ?? '',
            background: null,
            oldBackground: channel?.background,
          }
        : EMPTY
    );
  }, [channel]);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const data = new FormData();
      data.append('name', form.name);
      data.append('intro', form.intro);
      data.append('oldBackground', JSON.stringify(form.oldBackground));
      if (form.background) data.append('images', form.background);
      await updateChannel({ id: channel?._id, body: data });
    },
    [updateChannel, form, channel]
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

  return (
    <Dialog
      open={Boolean(channel)}
      onClose={close}
      title={t('update.title')}
      busy={isLoadingUpdate}
      footer={
        <>
          <Button variant='outline' onClick={close} disabled={isLoadingUpdate}>
            {t('common:actions.cancel')}
          </Button>
          <Button form='fu-update-channel' type='submit' loading={isLoadingUpdate}>
            {t('common:actions.save')}
          </Button>
        </>
      }
    >
      <form id='fu-update-channel' className='flex flex-col gap-4' onSubmit={handleSubmit}>
        <Field label={t('field.background')}>
          <ImageUpload
            value={form.background}
            existing={form.oldBackground}
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

export default UpdateChannelModal;
