import { useCallback, useContext, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { validateEmail } from '../../services/utils/validate';
import { useRegisterUserMutation } from '../../services/redux/query/api/usersApi';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { getWebInfo } from '../../services/redux/slice/userSlice';
import useMutationToast from '../../hooks/useMutationToast';
import AuthShell from '../auth/AuthShell';
import Button from '../../components/ui/Button';
import Field from '../../components/ui/Field';
import Input from '../../components/ui/Input';
import Textarea from '../../components/ui/Textarea';

function RegisterLayout() {
  const { t } = useTranslation('auth');
  const navigate = useNavigate();
  const webInfo = useSelector(getWebInfo);
  const { user } = useContext(FetchDataContext);
  const [
    register,
    {
      data: registerData,
      isLoading: isLoadingRegister,
      isSuccess: isSuccessRegister,
      isError: isErrorRegister,
      error: errorRegister,
    },
  ] = useRegisterUserMutation();
  const [isValidate, setIsValidate] = useState(false);
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    address: '',
    intro: '',
  });

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!validateEmail(form.email) || !form.email || !form.username) {
        setIsValidate(true);
      } else {
        setIsValidate(false);
        await register({ ...form });
      }
    },
    [form, register]
  );

  useMutationToast({
    data: registerData,
    error: errorRegister,
    isSuccess: isSuccessRegister,
    isError: isErrorRegister,
  });

  useEffect(() => {
    if (user !== null) navigate('/', { replace: true });
  }, [user, navigate]);

  const set = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }));

  return (
    <AuthShell title={t('register.title')} quote={webInfo?.website_quotes_register}>
      <form className='flex flex-col gap-4' onSubmit={handleSubmit} noValidate>
        <Field
          label={t('field.nameLabel')}
          required
          error={isValidate && !form.username ? t('validate.username') : ''}
        >
          {(aria) => (
            <Input
              {...aria}
              autoComplete='name'
              size='lg'
              placeholder={t('field.namePlaceholder')}
              value={form.username}
              onChange={set('username')}
            />
          )}
        </Field>

        <Field
          label={t('field.emailLabel')}
          required
          error={isValidate && !validateEmail(form.email) ? t('validate.email') : ''}
        >
          {(aria) => (
            <Input
              {...aria}
              type='email'
              autoComplete='email'
              size='lg'
              placeholder={t('field.emailPlaceholder')}
              value={form.email}
              onChange={set('email')}
            />
          )}
        </Field>

        <Field
          label={t('field.passwordLabel')}
          required
          error={isValidate && !form.password ? t('validate.password') : ''}
        >
          {(aria) => (
            <Input
              {...aria}
              type='password'
              autoComplete='new-password'
              size='lg'
              placeholder={t('field.passwordPlaceholder')}
              value={form.password}
              onChange={set('password')}
            />
          )}
        </Field>

        <Field label={t('field.addressLabel')} hint={t('field.optional')}>
          {(aria) => (
            <Input
              {...aria}
              size='lg'
              autoComplete='address-level1'
              placeholder={t('field.addressPlaceholder')}
              value={form.address}
              onChange={set('address')}
            />
          )}
        </Field>

        {/* Bản cũ đặt textarea `rows={10}` nhưng lại ép `h-[48px]`, nên ô giới
            thiệu cao đúng một dòng và không ai nhận ra nó nhập được nhiều dòng. */}
        <Field label={t('field.introLabel')} hint={t('field.optional')}>
          {(aria) => (
            <Textarea
              {...aria}
              rows={3}
              placeholder={t('field.introPlaceholder')}
              value={form.intro}
              onChange={set('intro')}
            />
          )}
        </Field>

        <Button type='submit' size='lg' block loading={isLoadingRegister} className='mt-2'>
          {t('register.submit')}
        </Button>

        <p className='mt-2 text-center text-sm text-fg-muted'>
          {t('register.hasAccount')}{' '}
          <button
            type='button'
            className='font-semibold text-accent-text underline-offset-4 hover:underline'
            onClick={() => navigate('/login')}
          >
            {t('register.toLogin')}
          </button>
        </p>
      </form>
    </AuthShell>
  );
}

export default RegisterLayout;
