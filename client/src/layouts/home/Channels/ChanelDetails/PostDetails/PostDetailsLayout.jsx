import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useGetPostDetailsQuery } from '../../../../../services/redux/query/usersQuery';
import Loading from '../../../../../components/ui/Loading';
import NotFoundLayout from '../../../../notfound/NotFoundLayout';
import SinglePost from '../../../../../components/ui/SinglePost';
import { FaArrowLeft } from 'react-icons/fa6';
function PostDetailsLayout() {
  const { id } = useParams();
  const navigate = useNavigate();
  const {
    data: postData,
    isSuccess: isSuccessPost,
    isError: isErrorPost,
    isLoading: isLoadingPost,
  } = useGetPostDetailsQuery(id);
  if (isLoadingPost) {
    return <Loading />;
  }
  if (isErrorPost) {
    return <NotFoundLayout />;
  }
  return (
    <main className='relative min-h-[100vh] dark:bg-neutral-900 flex flex-col gap-8 px-8 md:px-32 lg:px-64 text-neutral-700 dark:text-neutral-100 py-16 '>
      {isSuccessPost && (
        <>
          <button
            className='absolute top-16 left-4'
            aria-label='back-btn'
            onClick={() =>
              navigate(`/channels/${postData?.post?.channel?._id}`)
            }
          >
            <FaArrowLeft className='text-2xl' />
          </button>
          <section className='md:px-20 lg:px-32 xl:px-64'>
            <SinglePost post={postData?.post} />
          </section>
        </>
      )}
    </main>
  );
}

export default PostDetailsLayout;
