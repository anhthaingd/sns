import React, { Suspense, lazy, useContext } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import Page from '../../Page';
import {
  useFollowingUserMutation,
  useGetPostsFromAnotherUserQuery,
  useGetUserDetailsQuery,
} from '../../../services/redux/query/usersQuery';
import { FaPen } from 'react-icons/fa6';
import NotFoundLayout from '../../notfound/NotFoundLayout';
import { FetchDataContext } from '../../../context/FetchDataProvider';
import { FaHouseChimney } from 'react-icons/fa6';
import { ModalContext } from '../../../context/ModalProvider';
import SinglePost from '../../../components/ui/SinglePost';
import Pagination from '../../../components/ui/Pagination';
const UpdateProfileModal = lazy(() =>
  import('../../../components/modal/UpdateProfileModal')
);
function ProfileLayout() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const { user } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  const {
    data: userData,
    isLoading: isLoadingUser,
    isSuccess: isSuccessUser,
    isError: isErrorUser,
  } = useGetUserDetailsQuery(id);
  const [followingUser] = useFollowingUserMutation();
  const { data: postsData, isSuccess: isSuccessPosts } =
    useGetPostsFromAnotherUserQuery(
      {
        id: userData?.user?._id,
        search: `page=${searchParams.get('page') || 1}`,
      },
      { skip: !userData?.user }
    );
  if (isErrorUser) {
    return <NotFoundLayout />;
  }
  return (
    <Page>
      <>
        <Suspense>
          <UpdateProfileModal />
        </Suspense>
        {isSuccessUser && userData && (
          <div className='flex flex-col gap-8  md:px-16 lg:px-32'>
            <section className='w-full h-[420px] relative rounded-lg overflow-hidden'>
              <div className='relative w-full h-full'>
                <img
                  className='w-full h-full object-cover'
                  src={`${import.meta.env.VITE_BACKEND_URL}/${
                    userData?.user?.cover_bg?.url
                  }`}
                  alt='cover-bg'
                />
                <span
                  className='absolute top-0 left-0 w-full h-full'
                  style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}
                ></span>
              </div>
              <div className='absolute top-0 left-0 w-full h-full grid grid-cols-6 place-content-center gap-4 p-4'>
                <div
                  className='col-span-1 flex justify-center items-center overflow-hidden z-10'
                  aria-disabled={isLoadingUser}
                >
                  <img
                    className='size-[128px] rounded-full object-cover'
                    src={`${import.meta.env.VITE_BACKEND_URL}/${
                      userData?.user?.avatar?.url
                    }`}
                    alt={userData?.user?.username}
                    {...{ fetchPriority: 'high' }}
                  />
                </div>
                <div className='col-span-5 w-auto flex flex-col gap-2'>
                  <div className='h-[40px] flex justify-between items-center gap-4'>
                    <h1 className='text-lg md:text-xl font-bold text-neutral-100'>
                      {userData?.user?.username}
                    </h1>
                    {user?._id === userData?.user?._id && (
                      <button
                        className='absolute top-6 right-6 flex items-center gap-2 bg-neutral-200 dark:bg-neutral-700 px-4 py-2 rounded'
                        onClick={() =>
                          setVisibleModal('visibleUpdateProfileModal')
                        }
                      >
                        <FaPen />
                        <span>Edit Profile</span>
                      </button>
                    )}
                  </div>
                  <p className='capitalize text-neutral-100'>
                    {userData?.user?.role?.name}
                  </p>
                  <div className='w-full bg-neutral-200 dark:bg-neutral-800 rounded-md p-4 grid grid-cols-3'>
                    <div className='col-span-1'>
                      <p className='font-medium'>Posts</p>
                      <p>{userData?.posts}</p>
                    </div>
                    <div className='col-span-1'>
                      <p className='font-medium'>Followers</p>
                      <p>{userData?.followers?.length}</p>
                    </div>
                    <div className='col-span-1'>
                      <p className='font-medium'>Channels</p>
                      <p>{userData?.channels}</p>
                    </div>
                  </div>
                  {user?._id !== userData?.user?._id && (
                    <div className='my-4 grid grid-cols-2 gap-4'>
                      <button
                        className='col-span-1 border border-neutral-300 rounded py-3 font-bold text-neutral-100'
                        onClick={() =>
                          setVisibleModal({ visibleChatModal: userData?.user })
                        }
                      >
                        Chat
                      </button>
                      <button
                        className='col-span-1 bg-blue-700 rounded text-white font-bold'
                        onClick={() => followingUser(userData?.user?._id)}
                      >
                        {userData?.followers?.some((f) => f._id === user?._id)
                          ? 'Following'
                          : 'Follow'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </section>
            <section className='relative border border-neutral-300 dark:border-neutral-500 rounded-xl flex flex-col gap-8 px-4 py-8'>
              <div className='flex flex-col gap-2'>
                <h2 className='font-bold text-xl md:text-2xl'>Intro</h2>
                <p className='text-center font-medium'>
                  {userData?.user?.intro}
                </p>
              </div>
              <div className='flex flex-col gap-4'>
                <h2 className='font-bold text-xl md:text-2xl'>Details</h2>
                <div className='flex items-center gap-4'>
                  <FaHouseChimney className='text-2xl' />
                  <p>{userData?.user?.address}</p>
                </div>
              </div>
            </section>
            {isSuccessPosts && (
              <section className='py-8 flex flex-col gap-8 border border-neutral-300 dark:border-neutral-700 rounded-xl px-4'>
                <h2 className='text-2xl font-bold'>Posts</h2>
                <div className='flex flex-col gap-6'>
                  {postsData?.totalPage > 0 &&
                    postsData?.posts?.map((p) => {
                      return <SinglePost key={p._id} post={p} />;
                    })}
                </div>
                {postsData?.totalPage > 1 && (
                  <Pagination
                    curPage={searchParams.get('page') || 1}
                    totalPage={postsData?.totalPage}
                  />
                )}
              </section>
            )}
          </div>
        )}
      </>
    </Page>
  );
}

export default ProfileLayout;
