import React, { useContext, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  useGetChannelDetailsQuery,
  useJoinChannelMutation,
} from '../../../../services/redux/query/usersQuery';
import { HiUserGroup } from 'react-icons/hi';
import { IoLogOutOutline } from 'react-icons/io5';
import NotFoundLayout from '../../../notfound/NotFoundLayout';
import Loading from '../../../../components/ui/Loading';
import CreatePost from './components/CreatePost';
import ListsPost from './components/ListsPost';
import Page from '../../../Page';
import { format } from 'date-fns';
import { ModalContext } from '../../../../context/ModalProvider';

function ChannelDetailsLayout() {
  const navigate = useNavigate();
  const { setVisibleModal } = useContext(ModalContext);
  const { id } = useParams();

  const {
    data: channelData,
    isSuccess: isSuccessChannel,
    isLoading: isLoadingChannel,
    isError: isErrorChannel,
    error: errorChannel,
  } = useGetChannelDetailsQuery(id);

  const [
    joinChannel,
    {
      data: joinData,
      isSuccess: isSuccessJoin,
      isLoading: isLoadingJoin,
      isError: isErrorJoin,
      error: errorJoin,
    },
  ] = useJoinChannelMutation();

  useEffect(() => {
    if (isSuccessJoin && joinData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: joinData?.message,
        },
      });
      navigate('/', { replace: true });
    }
    if (isErrorJoin && errorJoin) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorJoin?.data?.message,
        },
      });
    }
  }, [
    isSuccessJoin,
    joinData,
    isErrorJoin,
    errorJoin,
    setVisibleModal,
    navigate,
  ]);

  if (isLoadingChannel) return <Loading />;
  if (isErrorChannel && errorChannel) return <NotFoundLayout />;

  return (
    <Page>
      <div className='min-h-[100vh] dark:bg-neutral-900 flex flex-col gap-8 text-neutral-700 dark:text-neutral-100'>
        {isSuccessChannel && channelData && (
          <>
            <section className='w-full rounded-lg overflow-hidden flex flex-col gap-4 border border-neutral-300 dark:border-neutral-600'>
              <div className='overflow-hidden'>
                <img
                  className='w-full h-[300px] object-cover'
                  src={`${import.meta.env.VITE_BACKEND_URL}/${
                    channelData?.channel?.background?.url
                  }`}
                  alt={channelData?.channel?.background?.name}
                />
              </div>
              <div className='p-4 flex flex-col gap-2'>
                <h1 className='text-xl md:text-3xl font-bold'>
                  {channelData?.channel?.name}
                </h1>
                <p>{channelData?.channel?.intro}</p>
              </div>
              <div className='p-4 grid grid-cols-3 border-t border-neutral-300 dark:borer-neutral-700 place-content-center place-items-center'>
                <div className='col-span-1 flex flex-col gap-4'>
                  <p className='text-lg font-medium'>
                    {channelData?.channel?.members?.length}{' '}
                    {channelData?.channel?.members?.length > 1
                      ? 'members'
                      : 'member'}
                  </p>
                  <div className='flex items-center'>
                    {channelData?.channel?.members?.slice(0, 8).map((m) => (
                      <div
                        key={m.id}
                        className='size-[32px] rounded-full overflow-hidden'
                      >
                        <img
                          className='w-full h-full object-cover'
                          src={`${import.meta.env.VITE_BACKEND_URL}/${
                            m?.avatar?.url
                          }`}
                          alt={m?.avatar?.name}
                          {...{ fetchPriority: 'low' }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
                <div className='col-span-1 flex flex-col gap-4'>
                  <p className='font-bold'>Created Day</p>
                  <p>
                    {format(
                      new Date(channelData?.channel?.created_at),
                      'dd/MM/yyyy'
                    )}
                  </p>
                </div>
                <div className='col-span-1 flex flex-col gap-4'>
                  <div className='flex items-center gap-2'>
                    <HiUserGroup className='text-2xl' />
                    <p className='font-bold'>Joined</p>
                  </div>
                  <div>
                    <button
                      className='flex items-center gap-2'
                      onClick={() =>
                        setVisibleModal({
                          visibleConfirmModal: {
                            question: `Are you sure you want to leave channel ${channelData?.channel?.name}?`,
                            description: 'Are you sure about your actions?',
                            loading: isLoadingJoin,
                            acceptFunc: () =>
                              joinChannel(channelData?.channel?._id),
                          },
                        })
                      }
                    >
                      <IoLogOutOutline className='text-2xl' />
                      <span className='font-bold'>Leave channel</span>
                    </button>
                  </div>
                </div>
              </div>
            </section>
            <section className='px-8 md:px-32'>
              <CreatePost channelId={channelData?.channel?._id} />
              <ListsPost channelId={channelData?.channel?._id} />
            </section>
          </>
        )}
      </div>
    </Page>
  );
}

export default ChannelDetailsLayout;
