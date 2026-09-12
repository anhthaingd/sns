import { useCallback, useContext, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaMagnifyingGlass, FaLayerGroup, FaArrowRight, FaPlus } from 'react-icons/fa6';
import Page from '../../../Page';
import {
  useGetAllChannelsQuery,
  useJoinChannelMutation,
} from '../../../../services/redux/query/api/channelsApi';
import useQueryString from '../../../../hooks/useQueryString';
import useMutationToast from '../../../../hooks/useMutationToast';
import { FetchDataContext } from '../../../../context/FetchDataProvider';
import Pagination from '../../../../components/ui/Pagination';
import Avatar from '../../../../components/ui/Avatar';
import Button from '../../../../components/ui/Button';
import Card from '../../../../components/ui/Card';
import EmptyState from '../../../../components/ui/EmptyState';
import SectionHeading from '../../../../components/ui/SectionHeading';
import { RowSkeleton } from '../../../../components/ui/Skeleton';
import mediaUrl from '../../../../services/utils/media';

function ChannelListLayout() {
  const { t } = useTranslation(['channel', 'common']);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, updateShortcut } = useContext(FetchDataContext);
  const [createQueryString, deleteQueryString] = useQueryString();
  const [searchValue, setSearchValue] = useState(searchParams.get('search') || '');
  const {
    data: channelsData,
    isSuccess: isSuccessChannels,
    isLoading,
  } = useGetAllChannelsQuery(
    `page=${searchParams.get('page') || 1}&search=${searchParams.get('search')}`
  );
  const [
    joinChannel,
    {
      data: joinData,
      isSuccess: isSuccessJoin,
      isError: isErrorJoin,
      error: errorJoin,
    },
  ] = useJoinChannelMutation();
  // Chỉ thẻ vừa được bấm mới quay, chứ không phải cả lưới: `isLoading` của
  // mutation là một cờ dùng chung, gắn nó vào mọi nút thì bấm tham gia một
  // channel sẽ làm toàn bộ danh sách hiện con quay cùng lúc.
  const [joiningId, setJoiningId] = useState(null);

  const checkJoinMember = useCallback(
    (channel) => channel?.members?.map((m) => m._id).includes(user?._id),
    [user?._id]
  );

  const handleRedirect = useCallback(
    async (c) => {
      if (checkJoinMember(c)) {
        navigate(`/channels/${c?._id}`);
        updateShortcut(c?._id);
        return;
      }
      setJoiningId(c?._id);
      try {
        await joinChannel(c?._id);
      } finally {
        setJoiningId(null);
      }
    },
    [checkJoinMember, joinChannel, navigate, updateShortcut]
  );

  const renderedChannels = useMemo(
    () =>
      isSuccessChannels &&
      channelsData?.channels?.map((c) => {
        const joined = checkJoinMember(c);
        const cover = mediaUrl(c?.background);
        return (
          <Card as='article' key={c._id} padded={false} className='overflow-hidden'>
            <div className='relative h-24 bg-gradient-to-br from-ai-700 to-asagi-700'>
              {cover ? (
                <img
                  className='size-full object-cover'
                  src={cover}
                  alt=''
                  loading='lazy'
                />
              ) : (
                <div
                  className='fu-seigaiha size-full text-white opacity-[0.14]'
                  aria-hidden='true'
                />
              )}
            </div>
            <div className='flex items-end gap-3 p-4'>
              <Avatar
                src={c?.background}
                name={c?.name}
                size='lg'
                ring
                className='-mt-9 rounded-xl ring-4'
              />
              <div className='min-w-0 flex-1'>
                <h2 className='truncate font-bold text-fg'>{c?.name}</h2>
                <p className='tnum truncate text-xs text-fg-subtle'>
                  {t('memberCount', { count: c?.members?.length || 0 })}
                </p>
              </div>
              <Button
                size='sm'
                variant={joined ? 'soft' : 'accent'}
                icon={joined ? FaArrowRight : FaPlus}
                loading={joiningId === c._id}
                onClick={() => handleRedirect(c)}
              >
                {joined ? t('detail.visit') : t('detail.join')}
              </Button>
            </div>
          </Card>
        );
      }),
    // `t` trong mảng phụ thuộc: đổi ngôn ngữ -> react-i18next trả `t` mới; thiếu
    // nó thì danh sách đã memo hoá giữ chữ của ngôn ngữ cũ.
    [isSuccessChannels, channelsData, checkJoinMember, handleRedirect, joiningId, t]
  );

  useMutationToast({
    data: joinData,
    error: errorJoin,
    isSuccess: isSuccessJoin,
    isError: isErrorJoin,
  });

  return (
    <Page rail={false}>
      <SectionHeading title={t('title')} />

      <form
        className='mt-5 flex gap-2'
        onSubmit={(e) => {
          e.preventDefault();
          createQueryString('search', searchValue);
        }}
      >
        <div className='relative min-w-0 flex-1 sm:max-w-sm'>
          <FaMagnifyingGlass
            className='pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-fg-subtle'
            aria-hidden='true'
          />
          <input
            className='h-10 w-full rounded-lg bg-surface pl-9 pr-3 text-sm text-fg ring-1 ring-inset ring-line transition-shadow placeholder:text-fg-subtle focus:ring-2 focus:ring-accent'
            type='search'
            placeholder={t('searchPlaceholder')}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </div>
        <Button type='submit'>{t('common:actions.search')}</Button>
        <Button
          type='button'
          variant='ghost'
          onClick={() => {
            setSearchValue('');
            deleteQueryString();
          }}
        >
          {t('common:actions.reset')}
        </Button>
      </form>

      <div className='mt-6'>
        {isLoading ? (
          <div aria-hidden='true' className='flex flex-col gap-2'>
            <RowSkeleton />
            <RowSkeleton />
            <RowSkeleton />
          </div>
        ) : channelsData?.channels?.length > 0 ? (
          <>
            <div className='grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3'>
              {renderedChannels}
            </div>
            <Pagination
              curPage={searchParams.get('page') || 1}
              totalPage={channelsData?.totalPage}
            />
          </>
        ) : (
          <EmptyState icon={FaLayerGroup} title={t('empty')} />
        )}
      </div>
    </Page>
  );
}

export default ChannelListLayout;
