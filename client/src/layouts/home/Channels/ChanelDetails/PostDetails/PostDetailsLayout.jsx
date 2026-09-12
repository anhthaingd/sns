import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaArrowLeft } from 'react-icons/fa6';
import Page from '../../../../Page';
import Loading from '../../../../../components/ui/Loading';
import Button from '../../../../../components/ui/Button';
import NotFoundLayout from '../../../../notfound/NotFoundLayout';
import SinglePost from '../../../../../components/ui/SinglePost';
import { useGetPostDetailsQuery } from '../../../../../services/redux/query/api/postsApi';

function PostDetailsLayout() {
  const { t } = useTranslation('common');
  const { id } = useParams();
  const navigate = useNavigate();
  const {
    data: postData,
    isSuccess: isSuccessPost,
    isError: isErrorPost,
    isLoading: isLoadingPost,
    refetch,
  } = useGetPostDetailsQuery(id);

  if (isLoadingPost) return <Loading />;
  if (isErrorPost) return <NotFoundLayout />;

  return (
    // Bản cũ dựng khung riêng, không có thanh điều hướng nào — mở một bài viết
    // là mất hết menu, chỉ còn đúng một mũi tên quay lại.
    <Page>
      <div className='mx-auto flex w-full max-w-feed flex-col gap-4'>
        <Button
          variant='ghost'
          size='sm'
          icon={FaArrowLeft}
          className='self-start'
          onClick={() => navigate(`/channels/${postData?.post?.channel?._id}`)}
        >
          {t('actions.back')}
        </Button>
        {isSuccessPost && <SinglePost post={postData?.post} changeData={refetch} />}
      </div>
    </Page>
  );
}

export default PostDetailsLayout;
