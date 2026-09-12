import { Suspense, lazy, useContext, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FaPlus,
  FaRegEye,
  FaRegPenToSquare,
  FaRegTrashCan,
  FaLayerGroup,
} from 'react-icons/fa6';
import {
  useDeleteChannelMutation,
  useGetAllChannelsQuery,
} from '../../../../services/redux/query/api/channelsApi';
import { ModalContext } from '../../../../context/ModalProvider';
import useQueryString from '../../../../hooks/useQueryString';
import useMutationToast from '../../../../hooks/useMutationToast';
import { formatDate } from '../../../../services/utils/format';
import Table from '../../../../components/ui/Table';
import Button from '../../../../components/ui/Button';
import IconButton from '../../../../components/ui/IconButton';
import EmptyState from '../../../../components/ui/EmptyState';
import SearchBar from '../../../../components/ui/SearchBar';
import Avatar from '../../../../components/ui/Avatar';

const AddChannelModal = lazy(() =>
  import('../../../../components/modal/AddChannelModal')
);
const UpdateChannelModal = lazy(() =>
  import('../../../../components/modal/UpdateChannelModal')
);
const ListMembersModal = lazy(() =>
  import('../../../../components/modal/ListMembersModal')
);

const cell = 'px-4 py-3 align-middle';

function Channels() {
  const { t } = useTranslation(['channel', 'common', 'admin']);
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const [createQueryString, deleteQueryString] = useQueryString();
  const { data: channelsData, isSuccess: isSuccessChannels } = useGetAllChannelsQuery(
    `page=${searchParams.get('page') || 1}&search=${searchParams.get('search')}`
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

  const rendered = useMemo(
    () =>
      isSuccessChannels &&
      channelsData?.channels?.map((c) => (
        <tr key={c._id}>
          <td className={cell}>
            <div className='flex items-center gap-2.5'>
              <Avatar
                src={c?.background}
                name={c?.name}
                size='sm'
                className='rounded-lg'
              />
              <span className='truncate font-medium text-fg'>{c.name}</span>
            </div>
          </td>
          <td className={`${cell} tnum text-right text-fg-muted`}>
            {c.members?.length ?? 0}
          </td>
          <td className={`${cell} tnum whitespace-nowrap text-fg-subtle`}>
            {formatDate(c?.created_at)}
          </td>
          <td className={cell}>
            <div className='flex items-center justify-end gap-1'>
              <IconButton
                size='sm'
                label={t('members.view')}
                onClick={() =>
                  setVisibleModal({
                    visibleListMembersModal: { channel: c?._id, members: c?.members },
                  })
                }
              >
                <FaRegEye className='size-3.5' />
              </IconButton>
              <IconButton
                size='sm'
                label={t('actions.update')}
                onClick={() => setVisibleModal({ visibleUpdateChannelModal: { ...c } })}
              >
                <FaRegPenToSquare className='size-3.5' />
              </IconButton>
              <IconButton
                size='sm'
                label={t('actions.delete')}
                className='hover:bg-danger-soft hover:text-danger-text'
                onClick={() =>
                  setVisibleModal({
                    visibleConfirmModal: {
                      tone: 'danger',
                      icon: <FaRegTrashCan />,
                      question: t('confirm.delete', { name: c?.name }),
                      description: t('common:confirm.irreversible'),
                      loading: isLoadingDelete,
                      acceptFunc: () => deleteChannel(c?._id),
                    },
                  })
                }
              >
                <FaRegTrashCan className='size-3.5' />
              </IconButton>
            </div>
          </td>
        </tr>
      )),
    // `t` phải nằm trong mảng phụ thuộc: đổi ngôn ngữ thì react-i18next trả về
    // một `t` mới, thiếu nó thì danh sách đã memo hoá giữ nguyên chữ của ngôn
    // ngữ cũ cho tới khi có thứ khác kích hoạt tính lại.
    [isSuccessChannels, channelsData, isLoadingDelete, deleteChannel, setVisibleModal, t]
  );

  useMutationToast({
    data: deleteData,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });

  return (
    <>
      <Suspense fallback={null}>
        <AddChannelModal />
        <UpdateChannelModal />
        <ListMembersModal />
      </Suspense>

      <div className='flex flex-col gap-4' aria-busy={isLoadingDelete}>
        <div className='flex flex-wrap items-center justify-between gap-3'>
          <SearchBar
            placeholder={t('searchPlaceholder')}
            initialValue={searchParams.get('search') || ''}
            onSearch={(value) => createQueryString('search', value)}
            onReset={deleteQueryString}
          />
          <Button
            icon={FaPlus}
            onClick={() => setVisibleModal('visibleAddChannelModal')}
          >
            {t('add.title')}
          </Button>
        </div>

        {isSuccessChannels && channelsData?.channels.length > 0 ? (
          <Table
            tHeader={[
              t('admin:table.name'),
              t('admin:table.members'),
              t('admin:table.createdAt'),
              t('admin:table.actions'),
            ]}
            renderedData={rendered}
            currPage={searchParams.get('page') || 1}
            totalPage={channelsData?.totalPage}
          />
        ) : (
          isSuccessChannels && <EmptyState icon={FaLayerGroup} title={t('empty')} />
        )}
      </div>
    </>
  );
}

export default Channels;
