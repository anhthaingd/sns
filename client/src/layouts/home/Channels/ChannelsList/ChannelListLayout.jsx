import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import Page from '../../../Page';
import {
  useGetAllChannelsQuery,
  useJoinChannelMutation,
} from '../../../../services/redux/query/usersQuery';
import { useNavigate, useSearchParams } from 'react-router-dom';
import useQueryString from '../../../../hooks/useQueryString';
import { FetchDataContext } from '../../../../context/FetchDataProvider';
import Pagination from '../../../../components/ui/Pagination';
import { ModalContext } from '../../../../context/ModalProvider';

function ChannelListLayout() {
  const navigate = useNavigate();
  const { setVisibleModal } = useContext(ModalContext);
  const [searchParams] = useSearchParams();
  const { user, updateShortcut } = useContext(FetchDataContext);
  const [createQueryString, deleteQueryString] = useQueryString();
  const [searchValue, setSearchValue] = useState('');
  const { data: channelsData, isSuccess: isSuccessChannels } =
    useGetAllChannelsQuery(
      `page=${searchParams.get('page') || 1}&search=${searchParams.get(
        'search'
      )}`
    );
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
  const checkJoinMember = useCallback(
    (channel) => {
      return channel?.members?.map((m) => m._id).includes(user?._id);
    },
    [user?._id]
  );
  const handleRedirect = useCallback(
    async (c) => {
      if (checkJoinMember(c)) {
        navigate(`/channels/${c?._id}`);
        updateShortcut(c?._id);
      } else {
        await joinChannel(c?._id);
      }
    },
    [user, joinChannel, navigate, updateShortcut]
  );
  const renderedChannels = useMemo(() => {
    return (
      isSuccessChannels &&
      channelsData?.channels?.map((c) => {
        return (
          <article className='flex gap-4' key={c._id}>
            <div className='size-[60px] rounded-lg overflow-hidden'>
              <img
                className='w-full h-full object-cover'
                src={`${import.meta.env.VITE_BACKEND_URL}/${
                  c?.background?.url
                }`}
                alt={c?.background?.name}
                {...{ fetchPriority: 'low' }}
              />
            </div>
            <div className='w-full flex justify-between items-center gap-4'>
              <div className='flex flex-col gap-1'>
                <p className='font-bold md:text-lg'>{c?.name}</p>
                <p className='font-medium'>
                  {c?.members?.length}{' '}
                  {c?.members?.length > 1 ? 'members' : 'member'}
                </p>
              </div>
              <button
                className={` px-4 py-2 rounded font-bold ${
                  checkJoinMember(c)
                    ? 'bg-neutral-200 dark:bg-neutral-700 dark:hover:bg-neutral-500 hover:bg-neutral-300'
                    : 'bg-blue-500 text-neutral-100 hover:bg-blue-300'
                } transition colors`}
                onClick={() => handleRedirect(c)}
              >
                {checkJoinMember(c) ? 'Visit' : 'Join'}
              </button>
            </div>
          </article>
        );
      })
    );
  }, [isSuccessChannels, channelsData, user]);
  useEffect(() => {
    if (isSuccessJoin && joinData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: joinData?.message,
        },
      });
    }
    if (isErrorJoin && errorJoin) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorJoin?.data?.message,
        },
      });
    }
  }, [isSuccessChannels, joinData, isErrorJoin, errorJoin, setVisibleModal]);
  return (
    <Page>
      <div
        className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-8'
        aria-disabled={isLoadingJoin}
      >
        <h1 className='text-xl md:text-2xl font-bold'>Channels</h1>
        <div className='w-full flex justify-end items-center gap-2'>
          <input
            className='px-4 py-2 border border-neutral-300 dark:border-neutral-700 rounded dark:bg-neutral-800'
            type='text'
            placeholder='Search channels...'
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
          <button
            className='px-4 py-2 font-bold bg-neutral-700 text-white rounded'
            onClick={deleteQueryString}
          >
            Reset
          </button>
          <button
            className='px-4 py-2 font-bold bg-blue-500 rounded text-neutral-100'
            onClick={() => createQueryString('search', searchValue)}
          >
            Search
          </button>
        </div>
        <div>
          {isSuccessChannels && channelsData?.channels?.length > 0 && (
            <div className='flex flex-col gap-4'>{renderedChannels}</div>
          )}
          {isSuccessChannels && channelsData?.channels?.length === 0 && (
            <div className='w-full flex justify-center items-center text-lg md:text-xl font-bold'>
              <p>No Channel Yet!</p>
            </div>
          )}
          {isSuccessChannels && channelsData?.totalPage > 1 && (
            <Pagination
              curPage={searchParams.get('page') || 1}
              totalPage={channelsData?.totalPage}
            />
          )}
        </div>
      </div>
    </Page>
  );
}

export default ChannelListLayout;
