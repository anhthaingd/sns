import React, {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useUpdateWebMutation } from '../../../../services/redux/query/webQuery';
import { useSelector } from 'react-redux';
import { getWebInfo } from '../../../../services/redux/slice/userSlice';
import { ModalContext } from '../../../../context/ModalProvider';
function Website() {
  const { setVisibleModal } = useContext(ModalContext);
  const webInfo = useSelector(getWebInfo);
  const [form, setForm] = useState({
    _id: '',
    logo: null,
    color_title: '',
    website_name: '',
    website_quotes_register: '',
    website_quotes_login: '',
  });
  const logoRef = useRef();
  const [selectedLogo, setSelectedLogo] = useState();
  const [selectedFileLogo, setSelectedFileLogo] = useState();
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
  useEffect(() => {
    setSelectedLogo(
      `${import.meta.env.VITE_BACKEND_URL}/${webInfo?.logo?.url}`
    );
    setForm({
      _id: webInfo?._id,
      logo: webInfo?.logo,
      color_title: webInfo?.color_title || '',
      website_name: webInfo?.website_name,
      website_quotes_register: webInfo?.website_quotes_register,
      website_quotes_login: webInfo?.website_quotes_login,
    });
  }, [webInfo]);
  const handleUploadImg = () => {
    if (logoRef.current) {
      logoRef.current.click();
    }
  };
  const handleChangeForm = useCallback(
    (e) => {
      const { name, value } = e.target;
      console.log(name, value);
      setForm((prevForm) => {
        return { ...prevForm, [name]: value };
      });
    },
    [form]
  );
  const handleFileSelect = useCallback(
    (e) => {
      const file = e.target.files?.[0];
      if (file) {
        setSelectedFileLogo(file);
        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target) {
            setSelectedLogo(e.target.result);
          }
        };
        reader.readAsDataURL(file);
      }
    },
    [handleUploadImg, selectedFileLogo, selectedLogo]
  );
  const handleCancelUpdate = useCallback(() => {
    setSelectedLogo(
      `${import.meta.env.VITE_BACKEND_URL}/${webInfo?.logo?.url}`
    );
    setForm({
      _id: webInfo?._id,
      website_name: webInfo?.website_name,
      color_title: webInfo?.color_title || '',
      website_quotes_register: webInfo?.website_quotes_register,
      website_quotes_login: webInfo?.website_quotes_login,
    });
  }, [form, selectedLogo, webInfo]);
  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const formData = new FormData();
      formData.append('website_name', form?.website_name);
      formData.append('color_title', form?.color_title);
      formData.append('website_quotes_register', form?.website_quotes_register);
      formData.append('website_quotes_login', form?.website_quotes_login);
      selectedFileLogo && formData?.append('images', selectedFileLogo);
      formData.append('oldLogo', JSON.stringify(form?.logo));
      await updateWeb({ id: form?._id, body: formData });
    },
    [updateWeb, form, selectedFileLogo]
  );
  console.log(form);
  useEffect(() => {
    if (isSuccessUpdate && updateData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: updateData?.message,
        },
      });
    }
    if (isErrorUpdate && errorUpdate) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorUpdate?.data?.message,
        },
      });
    }
  }, [
    isSuccessUpdate,
    updateData,
    isErrorUpdate,
    errorUpdate,
    setVisibleModal,
  ]);
  return (
    <section className='bg-neutral-100 dark:bg-neutral-800 rounded-lg p-4 md:p-6 mb-16'>
      <form onSubmit={handleSubmit}>
        <div className='grid grid-cols-12 text-darkGray dark:text-lightGray'>
          <div className='col-span-12 md:col-span-12 lg:col-span-12 mr-3'>
            <div className='lg:px-6 pt-4 lg:pl-40 lg:pr-40 md:pl-5 md:pr-5 flex-grow scrollbar-hide w-full max-h-full pb-0'>
              <div className='grid md:grid-cols-5 items-center sm:grid-cols-12 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
                <label
                  htmlFor='webId'
                  className='block text-sm md:text-base mb-1 sm:col-span-2 font-bold'
                >
                  Web Id
                </label>
                <div className='sm:col-span-3 flex flex-col gap-2'>
                  <input
                    className='block w-full h-12 px-3 py-1 text-sm focus:outline-none leading-5 rounded-md  dark:bg-neutral-700 mr-2 p-2'
                    type='text'
                    value={form?._id}
                    disabled
                  />
                </div>
              </div>
              <div className='grid md:grid-cols-5 items-center sm:grid-cols-12 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
                <label
                  htmlFor='website_name'
                  className='block text-sm md:text-base mb-1 sm:col-span-2 font-bold'
                >
                  Website Name
                </label>
                <div className='sm:col-span-3 flex flex-col gap-2'>
                  <input
                    name='website_name'
                    className='block w-full h-12 px-3 py-1 text-sm focus:outline-none leading-5 rounded-md  dark:bg-neutral-700 mr-2 p-2'
                    type='text'
                    value={form?.website_name}
                    onChange={handleChangeForm}
                  />
                </div>
              </div>
              <div className='grid md:grid-cols-5 items-center sm:grid-cols-12 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
                <label
                  htmlFor='color_title'
                  className='block text-sm md:text-base mb-1 sm:col-span-2 font-bold'
                >
                  Color for website name
                </label>
                <div className='sm:col-span-3 flex flex-col gap-2'>
                  <input
                    name='color_title'
                    className='block w-full h-12 px-3 py-1 text-sm focus:outline-none leading-5 rounded-md  dark:bg-neutral-700 mr-2 p-2'
                    type='color'
                    value={form?.color_title}
                    onChange={handleChangeForm}
                  />
                </div>
              </div>
              <div className='grid md:grid-cols-5 items-center sm:grid-cols-12 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
                <label
                  htmlFor=''
                  className='block text-sm md:text-base mb-1 sm:col-span-2 font-bold'
                >
                  Logo
                </label>
                <div className='sm:col-span-3 flex flex-col gap-4'>
                  <div className='flex justify-between items-center sm:flex-row flex-col gap-4'>
                    <img
                      className='w-auto max-h-[56px] object-contain'
                      src={selectedLogo}
                      alt={webInfo?.logo}
                    />
                    <input
                      name='logo'
                      accept='image/*,.jpeg,.jpg,.png,.webp'
                      type='file'
                      style={{ display: 'none' }}
                      ref={logoRef}
                      onChange={handleFileSelect}
                    />
                    <button
                      type='button'
                      className='w-[120px] bg-blue-500 px-4 py-2 text-sm rounded text-neutral-100'
                      onClick={handleUploadImg}
                    >
                      Change Logo
                    </button>
                  </div>
                  <p className='text-sm font-bold'>
                    Only *.jpeg, *.webp and *.png images will be accepted!
                  </p>
                </div>
              </div>
              <div className='grid md:grid-cols-5 items-center sm:grid-cols-12 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
                <label
                  htmlFor='website_quotes_register'
                  className='block text-sm md:text-base mb-1 sm:col-span-2 font-bold'
                >
                  Quotes Register
                </label>
                <div className='sm:col-span-3 flex flex-col gap-2'>
                  <input
                    name='website_quotes_register'
                    className='block w-full h-12 px-3 py-1 text-sm focus:outline-none leading-5 rounded-md  dark:bg-neutral-700 mr-2 p-2'
                    type='text'
                    value={form?.website_quotes_register}
                    onChange={handleChangeForm}
                  />
                </div>
              </div>
              <div className='grid md:grid-cols-5 items-center sm:grid-cols-12 gap-3 md:gap-5 xl:gap-6 lg:gap-6 mb-6'>
                <label
                  htmlFor='website_quotes_login'
                  className='block text-sm md:text-base mb-1 sm:col-span-2 font-bold'
                >
                  Quotes Login
                </label>
                <div className='sm:col-span-3 flex flex-col gap-2'>
                  <input
                    name='website_quotes_login'
                    className='block w-full h-12 px-3 py-1 text-sm focus:outline-none leading-5 rounded-md  dark:bg-neutral-700 mr-2 p-2'
                    type='text'
                    value={form?.website_quotes_login}
                    onChange={handleChangeForm}
                  />
                </div>
              </div>
              <div className='flex flex-col sm:flex-row justify-end  items-end sm:items-center gap-4'>
                <button
                  className={`w-full sm:w-[120px] h-[48px] py-2 px-8 rounded-md flex justify-center items-center border border-neutral-300 dark:border-neutral-600 bg-[#fff] hover:bg-[#FCC8D1] text-red-500 dark:bg-neutral-700 dark:text-red-500 dark:hover:bg-neutral-600 dark:hover:text-red-500 transition-colors ${
                    isLoadingUpdate ? 'cursor-not-allowed' : 'cursor-pointer'
                  }`}
                  type='button'
                  disabled={isLoadingUpdate}
                  onClick={handleCancelUpdate}
                >
                  Cancel
                </button>
                <button
                  className={`w-full sm:w-[160px] h-[48px] px-8 py-2 flex justify-center items-center rounded-lg bg-blue-500 text-white hover:bg-blue-700 transition-colors text-sm font-bold  ${
                    isLoadingUpdate ? 'cursor-not-allowed' : 'cursor-pointer'
                  }`}
                  type='submit'
                >
                  Update
                </button>
              </div>
            </div>
          </div>
        </div>
      </form>
    </section>
  );
}

export default Website;
