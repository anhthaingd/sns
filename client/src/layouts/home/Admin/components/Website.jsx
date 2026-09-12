import { useCallback, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { useUpdateWebMutation } from '../../../../services/redux/query/webQuery';
import { getWebInfo } from '../../../../services/redux/slice/userSlice';
import useMutationToast from '../../../../hooks/useMutationToast';
import Card from '../../../../components/ui/Card';
import Button from '../../../../components/ui/Button';
import Field from '../../../../components/ui/Field';
import Input from '../../../../components/ui/Input';
import Textarea from '../../../../components/ui/Textarea';
import ImageUpload from '../../../../components/ui/ImageUpload';

/**
 * Cấu hình website: tên, logo, màu tiêu đề, hai câu trích ở trang đăng
 * nhập / đăng ký.
 *
 * Bản cũ xếp các ô nhập vào lưới 12 cột kèm `lg:pl-40 lg:pr-40` cứng, nhãn ở
 * cột trái, và mỗi ô lại chỉ định class riêng. Ở đây dùng chung `Field` với
 * nhãn phía trên — đọc được trên điện thoại, và mọi ô có cùng chiều cao.
 */
function Website() {
  const { t } = useTranslation(['admin', 'common']);
  const webInfo = useSelector(getWebInfo);
  const [form, setForm] = useState({
    _id: '',
    logo: null,
    color_title: '',
    website_name: '',
    website_quotes_register: '',
    website_quotes_login: '',
  });
  const [selectedFileLogo, setSelectedFileLogo] = useState(null);
  const [
    updateWeb,
    {
      data: updateData,
      isLoading: isLoadingUpdate,
      isSuccess: isSuccessUpdate,
      isError: isErrorUpdate,
      error: errorUpdate,
    },
  ] = useUpdateWebMutation();

  const resetFromServer = useCallback(() => {
    setSelectedFileLogo(null);
    setForm({
      _id: webInfo?._id ?? '',
      logo: webInfo?.logo ?? null,
      color_title: webInfo?.color_title || '',
      website_name: webInfo?.website_name ?? '',
      website_quotes_register: webInfo?.website_quotes_register ?? '',
      website_quotes_login: webInfo?.website_quotes_login ?? '',
    });
  }, [webInfo]);

  useEffect(resetFromServer, [resetFromServer]);

  const handleChangeForm = useCallback((e) => {
    const { name, value } = e.target;
    setForm((prevForm) => ({ ...prevForm, [name]: value }));
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const formData = new FormData();
      formData.append('website_name', form?.website_name);
      formData.append('color_title', form?.color_title);
      formData.append('website_quotes_register', form?.website_quotes_register);
      formData.append('website_quotes_login', form?.website_quotes_login);
      if (selectedFileLogo) formData.append('images', selectedFileLogo);
      formData.append('oldLogo', JSON.stringify(form?.logo));
      await updateWeb({ id: form?._id, body: formData });
    },
    [updateWeb, form, selectedFileLogo]
  );

  useMutationToast({
    data: updateData,
    error: errorUpdate,
    isSuccess: isSuccessUpdate,
    isError: isErrorUpdate,
  });

  return (
    <Card as='form' onSubmit={handleSubmit} className='flex flex-col gap-5'>
      <div className='grid gap-5 lg:grid-cols-2'>
        <Field label={t('website.logo')} hint={t('website.logoHint')}>
          <ImageUpload
            aspect='aspect-square'
            value={selectedFileLogo}
            existing={form.logo}
            onChange={setSelectedFileLogo}
            onRemove={() => setSelectedFileLogo(null)}
            className='max-w-[14rem]'
          />
        </Field>

        <div className='flex flex-col gap-5'>
          <Field label={t('website.name')}>
            {(aria) => (
              <Input
                {...aria}
                name='website_name'
                value={form?.website_name}
                onChange={handleChangeForm}
              />
            )}
          </Field>

          <Field label={t('website.colorTitle')}>
            {(aria) => (
              <div className='flex items-center gap-2'>
                {/* Ô màu thật thay cho ô nhập chuỗi: bản cũ bắt gõ tay mã hex,
                    gõ sai một ký tự là tiêu đề website mất màu mà không báo gì. */}
                <input
                  type='color'
                  aria-label={t('website.colorTitle')}
                  className='size-10 shrink-0 cursor-pointer rounded-lg bg-surface p-1 ring-1 ring-inset ring-line'
                  value={form?.color_title || '#274A78'}
                  name='color_title'
                  onChange={handleChangeForm}
                />
                <Input
                  {...aria}
                  name='color_title'
                  className='font-mono'
                  value={form?.color_title}
                  onChange={handleChangeForm}
                />
              </div>
            )}
          </Field>

          <Field label={t('website.id')}>
            {(aria) => (
              <Input {...aria} className='font-mono' value={form?._id} disabled />
            )}
          </Field>
        </div>
      </div>

      <Field label={t('website.quotesLogin')}>
        {(aria) => (
          <Textarea
            {...aria}
            rows={2}
            name='website_quotes_login'
            value={form?.website_quotes_login}
            onChange={handleChangeForm}
          />
        )}
      </Field>

      <Field label={t('website.quotesRegister')}>
        {(aria) => (
          <Textarea
            {...aria}
            rows={2}
            name='website_quotes_register'
            value={form?.website_quotes_register}
            onChange={handleChangeForm}
          />
        )}
      </Field>

      <div className='flex justify-end gap-2 border-t border-line pt-4'>
        <Button
          type='button'
          variant='outline'
          onClick={resetFromServer}
          disabled={isLoadingUpdate}
        >
          {t('common:actions.reset')}
        </Button>
        <Button type='submit' loading={isLoadingUpdate}>
          {t('common:actions.save')}
        </Button>
      </div>
    </Card>
  );
}

export default Website;
