import {
  Suspense,
  lazy,
  useContext,
  useMemo,
  useState,
} from 'react';
import { useDeleteChannelMutation, useGetAllChannelsQuery } from '../../../../services/redux/query/api/channelsApi';
import { useSearchParams } from 'react-router-dom';
import Table from '../../../../components/ui/Table';
import NotFoundItem from '../../../../components/ui/NotFoundItem';
import useQueryString from '../../../../hooks/useQueryString';
import { formatDate } from '../../../../services/utils/format';
import {
  FaRegTrashCan,
  FaRegPenToSquare,
  FaPlus,
  FaRegEye,
} from 'react-icons/fa6';
import { ModalContext } from '../../../../context/ModalProvider';
import useMutationToast from '../../../../hooks/useMutationToast';
import { useTranslation } from 'react-i18next';
const AddChannelModal = lazy(() =>
  import('../../../../components/modal/AddChannelModal')
);
const UpdateChannelModal = lazy(() =>
  import('../../../../components/modal/UpdateChannelModal')
);
const ListMembersModal = lazy(() =>
  import('../../../../components/modal/ListMembersModal')
);
function Channels() {
  const { t } = useTranslation(['channel', 'common']);
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const [createQueryString, deleteQueryString] = useQueryString();
  const [searchValue, setSearchValue] = useState('');
  const { data: channelsData, isSuccess: isSuccessChannels } =
    useGetAllChannelsQuery(
      `page=${searchParams.get('page') || 1}&search=${searchParams.get(
        'search'
      )}`
    );
  const [
    deleteChannel,
    {
      data: deleteData,
      isSuccess: isSuccessDelete,
      isLoading: isLoadingDelete,
      isError: isErrorDelete,
      error: errorDelete,
    },
  ] = useDeleteChannelMutation();
  const rendered = useMemo(() => {
    return (
      isSuccessChannels &&
      channelsData?.channels?.map((c) => {
        return (
          <tr key={c._id}>
            <td
              title={c._id}
              className='p-4 text-center truncate max-w-[120px]'
            >
              {c._id}
            </td>
            <td className='p-4 text-center'>{c.name}</td>
            <td className='p-4 text-center'>{c.members?.length}</td>
            <td className='p-4 text-center'>{formatDate(c?.created_at)}</td>
            <td className='p-4'>
              <div className='flex justify-center items-center gap-[12px]'>
                <button
                  title={t('members.view')}
                  className='text-lg flex justify-center items-center hover:text-green-500 transition-colors'
                  aria-label={t('members.view')}
                  onClick={() =>
                    setVisibleModal({
                      visibleListMembersModal: {
                        channel: c?._id,
                        members: c?.members,
                      },
                    })
                  }
                >
                  <FaRegEye />
                </button>
                <button
                  title={t('actions.update')}
                  className='text-lg flex justify-center items-center hover:text-green-500 transition-colors'
                  aria-label={t('actions.update')}
                  onClick={() =>
                    setVisibleModal({
                      visibleUpdateChannelModal: { ...c },
                    })
                  }
                >
                  <FaRegPenToSquare />
                </button>
                <button
                  title={t('actions.delete')}
                  className='text-lg flex justify-center items-center hover:text-red-500 transition-colors'
                  aria-label={t('actions.delete')}
                  onClick={() =>
                    setVisibleModal({
                      visibleConfirmModal: {
                        icon: <FaRegTrashCan className='text-red-500' />,
                        question: t('confirm.delete', { name: c?.name }),
                        description: t('common:confirm.irreversible'),
                        loading: isLoadingDelete,
                        acceptFunc: () => deleteChannel(c?._id),
                      },
                    })
                  }
                >
                  <FaRegTrashCan />
                </button>
              </div>
            </td>
          </tr>
        );
      })
    );
  // `t` phải nằm trong mảng phụ thuộc: đổi ngôn ngữ thì react-i18next trả về
  // một `t` mới, thiếu nó thì danh sách đã memo hoá giữ nguyên chữ của ngôn
  // ngữ cũ cho tới khi có thứ khác kích hoạt tính lại.
  }, [isSuccessChannels, channelsData, t]);
  useMutationToast({
    data: deleteData,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });
  return (
    <>
      <Suspense>
        <AddChannelModal />
        <UpdateChannelModal />
        <ListMembersModal />
      </Suspense>
      <div className='flex flex-col gap-8' aria-disabled={isLoadingDelete}>
        <div className='flex justify-between'>
          <h1 className='text-lg md:text-xl font-bold'>{t('title')}</h1>
          <button
            className='px-4 py-2 font-bold bg-neutral-700 hover:bg-blue-500 transition-colors text-white rounded flex items-center gap-2'
            onClick={() => setVisibleModal('visibleAddChannelModal')}
          >
            <FaPlus className='text-lg' />
            <span>{t('add.title')}</span>
          </button>
        </div>
        <div className='w-full flex items-center gap-2'>
          <input
            className='px-4 py-2 border border-neutral-300 dark:border-neutral-700 rounded dark:bg-neutral-800'
            type='text'
            placeholder={t('searchPlaceholder')}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
          <button
            className='px-4 py-2 font-bold bg-neutral-700 text-white rounded'
            onClick={deleteQueryString}
          >{t('common:actions.reset')}</button>
          <button
            className='px-4 py-2 font-bold bg-blue-500 rounded text-neutral-100'
            onClick={() => createQueryString('search', searchValue)}
          >{t('common:actions.search')}</button>
        </div>
        {isSuccessChannels && channelsData?.channels.length > 0 && (
          <Table
            tHeader={['id', 'name', 'members', 'created at', 'actions']}
            renderedData={rendered}
            currPage={searchParams.get('page') || 1}
            totalPage={channelsData?.totalPage}
          />
        )}
        {isSuccessChannels && channelsData?.channels?.length === 0 && (
          <NotFoundItem message={t('empty')} />
        )}
      </div>
    </>
  );
}

export default Channels;
