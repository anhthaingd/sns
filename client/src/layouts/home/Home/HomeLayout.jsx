import Page from '../../Page';
import PostComposer from '../../../components/post/PostComposer';
import ListsPost from './components/ListsPost';

/**
 * Bảng tin.
 *
 * Cột bài viết bị giới hạn ở `max-w-feed` (640px) chứ không giãn hết khung:
 * dòng văn bản dài quá ~75 ký tự thì mắt khó bắt được đầu dòng kế tiếp.
 */
function HomeLayout() {
  return (
    <Page>
      <div className='mx-auto flex w-full max-w-feed flex-col gap-4'>
        <PostComposer />
        <ListsPost />
      </div>
    </Page>
  );
}

export default HomeLayout;
