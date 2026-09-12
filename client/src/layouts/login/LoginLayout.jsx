import { useCallback, useContext, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { validateEmail } from '../../services/utils/validate';
import { useLoginUserMutation } from '../../services/redux/query/api/usersApi';
import { getWebInfo, setToken } from '../../services/redux/slice/userSlice';
import { FetchDataContext } from '../../context/FetchDataProvider';
import useMutationToast from '../../hooks/useMutationToast';
import AuthShell from '../auth/AuthShell';
import Button from '../../components/ui/Button';
import Field from '../../components/ui/Field';
import Input from '../../components/ui/Input';

function LoginLayout() {
  const { t } = useTranslation('auth');
  const webInfo = useSelector(getWebInfo);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useContext(FetchDataContext);
  const [
    login,
    {
      data: loginData,
      isLoading: isLoadingLogin,
      isSuccess: isSuccessLogin,
      isError: isErrorLogin,
      error: errorLogin,
    },
  ] = useLoginUserMutation();
  const [isValidate, setIsValidate] = useState(false);
  const [form, setForm] = useState({ email: '', password: '' });

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!validateEmail(form.email) || !form.email) {
        setIsValidate(true);
      } else {
        setIsValidate(false);
        await login({ email: form.email, password: form.password });
      }
    },
    [form, login]
  );

  useMutationToast(
    { data: loginData, error: errorLogin, isSuccess: isSuccessLogin, isError: isErrorLogin },
    {
      // Đăng nhập xong là chuyển sang trang chủ ngay, toast thành công chỉ kịp
      // loé lên rồi mất cùng trang cũ.
      showSuccess: false,
      onSuccess: (data) => dispatch(setToken(data?.accessToken)),
    }
  );

  useEffect(() => {
    if (user !== null) navigate('/', { replace: true });
  }, [user, navigate]);

  const emailError = isValidate && !validateEmail(form.email) ? t('validate.email') : '';
  const passwordError = isValidate && !form.password ? t('validate.password') : '';

  return (
    <AuthShell title={t('login.title')} quote={webInfo?.website_quotes_login}>
      <form className='flex flex-col gap-4' onSubmit={handleSubmit} noValidate>
        <Field label={t('field.emailLabel')} error={emailError}>
          {(aria) => (
            <Input
              {...aria}
              type='email'
              autoComplete='email'
              size='lg'
              placeholder={t('field.emailPlaceholder')}
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          )}
        </Field>

        <Field label={t('field.passwordLabel')} error={passwordError}>
          {(aria) => (
            <Input
              {...aria}
              type='password'
              autoComplete='current-password'
              size='lg'
              placeholder={t('field.passwordPlaceholder')}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          )}
        </Field>

        <Button type='submit' size='lg' block loading={isLoadingLogin} className='mt-2'>
          {t('login.submit')}
        </Button>

        <p className='mt-2 text-center text-sm text-fg-muted'>
          {t('login.noAccount')}{' '}
          <button
            type='button'
            className='font-semibold text-accent-text underline-offset-4 hover:underline'
            onClick={() => navigate('/register')}
          >
            {t('login.toRegister')}
          </button>
        </p>
      </form>
    </AuthShell>
  );
}

export default LoginLayout;
