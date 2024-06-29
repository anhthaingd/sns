import React, { useCallback, useContext, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import bgImg from '@/assets/pexels-photo-4881619.webp';
import { validateEmail } from '../../services/utils/validate';
import { ModalContext } from '../../context/ModalProvider';
import { useRegisterUserMutation } from '../../services/redux/query/usersQuery';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { getWebInfo } from '../../services/redux/slice/userSlice';
function RegisterLayout() {
  const navigate = useNavigate();
  const webInfo = useSelector(getWebInfo);
  const { user } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
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
    [isValidate, form, register]
  );
  useEffect(() => {
    if (isSuccessRegister && registerData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: registerData?.message,
        },
      });
    }

    if (isErrorRegister && errorRegister) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorRegister?.data?.message,
        },
      });
    }
  }, [
    isSuccessRegister,
    registerData,
    isErrorRegister,
    errorRegister,
    setVisibleModal,
  ]);
  useEffect(() => {
    if (user !== null) {
      return navigate('/', { replace: true });
    }
  }, [user, navigate]);
  return (
    <div className='absolute w-full h-full top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 overflow-hidden flex justify-center items-center bg-violet-200 text-neutral-700 px-4 sm:px-0'>
      <section
        className='w-full sm:w-4/5 lg:w-1/2 m-auto h-4/5 overflow-hidden rounded-xl grid grid-cols-1 lg:grid-cols-2 text-sm md:text-base'
        aria-disabled={isLoadingRegister}
      >
        <form
          className='bg-white flex flex-col justify-center px-8 md:px-16 gap-6 md:gap-8'
          onSubmit={handleSubmit}
        >
          <h1 className='text-center lg:text-start text-4xl font-bold'>
            Register
          </h1>
          <div className='w-full flex flex-col gap-6'>
            <div className='w-full flex flex-col gap-2'>
              <input
                className='h-[48px] px-4 py-2 border border-neutral-300 rounded'
                type='text'
                placeholder='Enter your name...'
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
              />
              {isValidate && !form.username && (
                <p className='font-bold text-red-500 text-sm'>
                  Username can't be null!
                </p>
              )}
            </div>
            <div className='w-full flex flex-col gap-2'>
              <input
                className='h-[48px] px-4 py-2 border border-neutral-300 rounded'
                type='text'
                placeholder='Enter your email...'
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
              {isValidate && !validateEmail(form.email) && (
                <p className='font-bold text-red-500 text-sm'>
                  Email was wrong!
                </p>
              )}
            </div>
            <div className='w-full flex flex-col gap-2'>
              <input
                className='h-[48px] px-4 py-2 border border-neutral-300 rounded'
                type='password'
                placeholder='Enter your password...'
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
              {isValidate && !form.password && (
                <p className='font-bold text-red-500 text-sm'>
                  Password cant't be null
                </p>
              )}
            </div>
            <div className='w-full flex flex-col gap-2'>
              <input
                className='h-[48px] px-4 py-2 border border-neutral-300 rounded'
                type='text'
                placeholder='Enter your address...'
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </div>
            <div className='w-full flex flex-col gap-2'>
              <textarea
                className='h-[48px] px-4 py-2 border border-neutral-300 rounded'
                placeholder='Enter your intro...'
                value={form.intro}
                rows={10}
                onChange={(e) => setForm({ ...form, intro: e.target.value })}
              />
            </div>
          </div>
          <button
            className='h-[48px] bg-neutral-700 text-white font-bold rounded hover:bg-violet-500 transition-colors'
            type='submit'
          >
            Register
          </button>
          <div className='flex items-center gap-2'>
            <p className='font-bold'>Already have an account?</p>
            <button
              className='text-violet-500 font-bold'
              type='button'
              onClick={() => navigate('/login')}
            >
              Login
            </button>
          </div>
        </form>
        <div className='hidden lg:flex relative'>
          <img src={bgImg} alt='' {...{ fetchPriority: 'high' }} />
          <div
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            className='absolute top-0 left-0 z-10 w-full h-full flex flex-col justify-center items-center gap-8 px-4'
          >
            <h1 className='text-neutral-100 text-4xl font-bold'>
              {webInfo?.website_name}
            </h1>
            <p className='text-neutral-100 font-bold italic'>
              " {webInfo?.website_quotes_register} "
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default RegisterLayout;
