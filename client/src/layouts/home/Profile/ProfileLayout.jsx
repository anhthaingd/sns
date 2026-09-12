import { Suspense, lazy, useContext } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaPen, FaHouseChimney, FaRegComment, FaUserPlus, FaCheck } from 'react-icons/fa6';
import Page from '../../Page';
import NotFoundLayout from '../../notfound/NotFoundLayout';
import { FetchDataContext } from '../../../context/FetchDataProvider';
import { ModalContext } from '../../../context/ModalProvider';
import {
  useFollowingUserMutation,
  useGetUserDetailsQuery,
} from '../../../services/redux/query/api/usersApi';
import { useGetPostsFromAnotherUserQuery } from '../../../services/redux/query/api/postsApi';
import SinglePost from '../../../components/ui/SinglePost';
import Pagination from '../../../components/ui/Pagination';
import Avatar from '../../../components/ui/Avatar';
import Button from '../../../components/ui/Button';
import Card from '../../../components/ui/Card';
import EmptyState from '../../../components/ui/EmptyState';
import { SkeletonList } from '../../../components/ui/Skeleton';
import mediaUrl from '../../../services/utils/media';

const UpdateProfileModal = lazy(() =>
  import('../../../components/modal/UpdateProfileModal')
);

/** Một ô số liệu trong dải thống kê dưới tên người dùng. */
function Stat({ label, value }) {
  return (
    <div className='flex flex-col items-center px-4 sm:items-start'>
      <span className='tnum font-display text-lg font-black text-fg'>
        {value ?? 0}
      </span>
      <span className='text-2xs font-semibold uppercase tracking-wider text-fg-subtle'>
        {label}
      </span>
    </div>
  );
}

function ProfileLayout() {
  const { t } = useTranslation(['user', 'post']);
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const { user } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  const {
    data: userData,
    isSuccess: isSuccessUser,
    isError: isErrorUser,
  } = useGetUserDetailsQuery(id);
  const [followingUser] = useFollowingUserMutation();
  const {
    data: postsData,
    isSuccess: isSuccessPosts,
    isLoading: isLoadingPosts,
    refetch: refetchPosts,
  } = useGetPostsFromAnotherUserQuery(
    {
      id: userData?.user?._id,
      search: `page=${searchParams.get('page') || 1}`,
    },
    { skip: !userData?.user }
  );

  if (isErrorUser) return <NotFoundLayout />;
  if (!isSuccessUser || !userData) {
    return (
      <Page>
        <SkeletonList count={2} />
      </Page>
    );
  }

  const profile = userData.user;
  const isMe = user?._id === profile?._id;
  const isFollowing = userData?.followers?.some((f) => f._id === user?._id);
  const cover = mediaUrl(profile?.cover_bg);

  return (
    <Page>
      <Suspense fallback={null}>
        <UpdateProfileModal />
      </Suspense>

      <div className='flex flex-col gap-4'>
        {/* Đầu trang: ảnh bìa + ảnh đại diện chồng lên mép dưới.
            Bản cũ phủ một lớp đen 60% lên ảnh bìa rồi đặt TOÀN BỘ thông tin lên
            trên, nên ảnh bìa vừa không nhìn được vừa làm chữ khó đọc. */}
        <Card padded={false} className='overflow-hidden'>
          <div className='relative h-36 bg-gradient-to-br from-ai-700 via-ai-800 to-asagi-800 sm:h-48'>
            {cover ? (
              <img
                className='size-full object-cover'
                src={cover}
                alt={t('profile.coverAlt')}
              />
            ) : (
              <div
                className='fu-seigaiha size-full text-white opacity-[0.12]'
                aria-hidden='true'
              />
            )}
          </div>

          <div className='px-4 pb-4 sm:px-6 sm:pb-6'>
            <div className='-mt-10 flex flex-wrap items-end justify-between gap-4 sm:-mt-12'>
              <Avatar
                src={profile?.avatar}
                name={profile?.username}
                size='2xl'
                ring
                className='ring-4'
              />
              <div className='flex flex-wrap gap-2 pb-1'>
                {isMe ? (
                  <Button
                    variant='outline'
                    size='sm'
                    icon={FaPen}
                    onClick={() => setVisibleModal('visibleUpdateProfileModal')}
                  >
                    {t('profile.edit')}
                  </Button>
                ) : (
                  <>
                    <Button
                      variant='outline'
                      size='sm'
                      icon={FaRegComment}
                      onClick={() => setVisibleModal({ visibleChatModal: profile })}
                    >
                      {t('profile.chat')}
                    </Button>
                    <Button
                      variant={isFollowing ? 'soft' : 'accent'}
                      size='sm'
                      icon={isFollowing ? FaCheck : FaUserPlus}
                      onClick={() => followingUser(profile?._id)}
                    >
                      {isFollowing ? t('actions.unfollow') : t('actions.follow')}
                    </Button>
                  </>
                )}
              </div>
            </div>

            <div className='mt-3'>
              <h1 className='text-xl font-bold text-fg sm:text-2xl'>
                {profile?.username}
              </h1>
              <p className='text-sm capitalize text-fg-subtle'>
                {profile?.role?.name}
              </p>
            </div>

            <div className='mt-4 flex divide-x divide-line border-t border-line pt-4'>
              <Stat label={t('profile.posts')} value={userData?.posts} />
              <Stat
                label={t('profile.followers')}
                value={userData?.followers?.length}
              />
              <Stat label={t('profile.channels')} value={userData?.channels} />
            </div>
          </div>
        </Card>

        <div className='grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)] lg:items-start'>
          {/* Cột giới thiệu dính khi cuộn, để danh sách bài viết dài không kéo
              người đọc rời khỏi thông tin về chủ trang. */}
          <Card className='flex flex-col gap-4 lg:sticky lg:top-[calc(theme(spacing.header)+1.25rem)]'>
            <div>
              <h2 className='text-base font-bold text-fg'>{t('profile.intro')}</h2>
              <p className='mt-1.5 whitespace-pre-line text-sm leading-relaxed text-fg-muted'>
                {profile?.intro || t('profile.noIntro')}
              </p>
            </div>
            <div className='border-t border-line pt-4'>
              <h2 className='text-base font-bold text-fg'>{t('profile.details')}</h2>
              <p className='mt-2 flex items-center gap-2.5 text-sm text-fg-muted'>
                <FaHouseChimney className='size-4 shrink-0 text-fg-subtle' aria-hidden='true' />
                {profile?.address || t('profile.noAddress')}
              </p>
            </div>
          </Card>

          <section className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('profile.posts')}</h2>
            {isLoadingPosts && <SkeletonList count={2} />}
            {isSuccessPosts && postsData?.posts?.length > 0 ? (
              <>
                {postsData.posts.map((p) => (
                  // `changeData` là bắt buộc: SinglePost gọi nó sau mỗi lượt
                  // thích / lưu / bình luận. Bản cũ không truyền, nên mọi thao
                  // tác trên bài viết ở trang cá nhân đều ném TypeError.
                  <SinglePost key={p._id} post={p} changeData={refetchPosts} />
                ))}
                <Pagination
                  curPage={searchParams.get('page') || 1}
                  totalPage={postsData?.totalPage}
                />
              </>
            ) : (
              isSuccessPosts && <EmptyState title={t('post:empty')} />
            )}
          </section>
        </div>
      </div>
    </Page>
  );
}

export default ProfileLayout;
