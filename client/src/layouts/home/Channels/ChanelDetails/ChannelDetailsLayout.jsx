import { useContext } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaUserGroup, FaCalendarDay, FaRightFromBracket } from 'react-icons/fa6';
import Page from '../../../Page';
import NotFoundLayout from '../../../notfound/NotFoundLayout';
import Loading from '../../../../components/ui/Loading';
import Avatar from '../../../../components/ui/Avatar';
import Button from '../../../../components/ui/Button';
import Card from '../../../../components/ui/Card';
import PostComposer from '../../../../components/post/PostComposer';
import ListsPost from './components/ListsPost';
import {
  useGetChannelDetailsQuery,
  useJoinChannelMutation,
} from '../../../../services/redux/query/api/channelsApi';
import { ModalContext } from '../../../../context/ModalProvider';
import useMutationToast from '../../../../hooks/useMutationToast';
import { formatShortDate } from '../../../../services/utils/format';
import mediaUrl from '../../../../services/utils/media';

/** Số thành viên hiện dưới dạng chồng ảnh đại diện. */
const MAX_FACES = 8;

function ChannelDetailsLayout() {
  const { t } = useTranslation(['channel', 'common']);
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

  useMutationToast(
    { data: joinData, error: errorJoin, isSuccess: isSuccessJoin, isError: isErrorJoin },
    // Rời channel xong thì trang này không còn gì để xem nữa.
    { onSuccess: () => navigate('/', { replace: true }) }
  );

  if (isLoadingChannel) return <Loading />;
  if (isErrorChannel && errorChannel) return <NotFoundLayout />;
  if (!isSuccessChannel || !channelData) return null;

  const channel = channelData.channel;
  const members = channel?.members ?? [];
  const cover = mediaUrl(channel?.background);

  return (
    <Page>
      <div className='mx-auto flex w-full max-w-feed flex-col gap-4'>
        <Card padded={false} className='overflow-hidden'>
          <div className='relative h-40 bg-gradient-to-br from-ai-700 via-ai-800 to-asagi-800 sm:h-56'>
            {cover ? (
              <img
                className='size-full object-cover'
                src={cover}
                alt=''
              />
            ) : (
              <div
                className='fu-seigaiha size-full text-white opacity-[0.12]'
                aria-hidden='true'
              />
            )}
          </div>

          <div className='p-4 sm:p-5'>
            <h1 className='text-xl font-bold text-fg sm:text-2xl'>{channel?.name}</h1>
            {channel?.intro && (
              <p className='mt-1.5 text-sm leading-relaxed text-fg-muted'>
                {channel.intro}
              </p>
            )}

            <div className='mt-4 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-4'>
              <div className='flex flex-wrap items-center gap-x-6 gap-y-3'>
                <div>
                  <p className='flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-wider text-fg-subtle'>
                    <FaUserGroup className='size-3' aria-hidden='true' />
                    {/* Bản cũ ghép tay chuỗi 'member'/'members' bằng tiếng Anh
                        ngay trong JSX, nên ô này luôn là tiếng Anh kể cả khi
                        giao diện đang chạy tiếng Nhật. */}
                    {t('memberCount', { count: members.length })}
                  </p>
                  <div className='mt-1.5 flex -space-x-2'>
                    {members.slice(0, MAX_FACES).map((m) => (
                      <Avatar
                        key={m._id}
                        src={m?.avatar}
                        name={m?.username}
                        size='sm'
                        ring
                      />
                    ))}
                    {members.length > MAX_FACES && (
                      <span className='tnum flex size-8 items-center justify-center rounded-full bg-surface-3 text-2xs font-bold text-fg-muted ring-2 ring-surface'>
                        +{members.length - MAX_FACES}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <p className='flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-wider text-fg-subtle'>
                    <FaCalendarDay className='size-3' aria-hidden='true' />
                    {t('detail.createdDay')}
                  </p>
                  <p className='tnum mt-1.5 text-sm font-semibold text-fg'>
                    {formatShortDate(channel?.created_at)}
                  </p>
                </div>
              </div>

              <Button
                variant='ghost'
                size='sm'
                icon={FaRightFromBracket}
                className='text-danger-text hover:bg-danger-soft'
                onClick={() =>
                  setVisibleModal({
                    visibleConfirmModal: {
                      tone: 'danger',
                      question: t('confirm.leave', { name: channel?.name }),
                      description: t('common:confirm.areYouSure'),
                      loading: isLoadingJoin,
                      acceptFunc: () => joinChannel(channel?._id),
                    },
                  })
                }
              >
                {t('detail.leave')}
              </Button>
            </div>
          </div>
        </Card>

        <PostComposer channelId={channel?._id} />
        <ListsPost channelId={channel?._id} />
      </div>
    </Page>
  );
}

export default ChannelDetailsLayout;
