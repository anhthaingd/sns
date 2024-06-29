import React, { useContext } from 'react';
import { useGetSearchUsersQuery } from '../../../../services/redux/query/usersQuery';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Pagination from '../../../../components/ui/Pagination';
import { ModalContext } from '../../../../context/ModalProvider';

function Users({ searchValue }) {
  const navigate = useNavigate();
  const { setVisibleModal } = useContext(ModalContext);
  const [searchParams] = useSearchParams();
  const { data: usersData, isSuccess: isSuccessUsers } = useGetSearchUsersQuery(
    `page=${searchParams.get('page') || 1}&search=${searchValue}`,
    { skip: !searchValue }
  );
  return (
    <div className='bg-neutral-100 dark:bg-neutral-800 p-4 rounded'>
      <div className='flex justify-between items-center gap-4'>
        <h1 className='text-xl md:text-2xl font-bold dark:text-white'>
          People
        </h1>
        {isSuccessUsers && (
          <p className='text-medium text-lg'>
            Found {usersData?.totalUsers}{' '}
            {usersData?.totalUsers > 1 ? 'Results' : 'Result'}
          </p>
        )}
      </div>
      {isSuccessUsers && usersData?.users?.length > 0 && (
        <div className='my-8'>
          <div className='flex flex-col gap-8'>
            {usersData?.users?.map((u) => {
              return (
                <article className='flex gap-4' key={u._id}>
                  <div className='size-[42px] rounded-full overflow-hidden'>
                    <img
                      className='w-full h-full object-cover'
                      src={`${import.meta.env.VITE_BACKEND_URL}/${
                        u?.avatar?.url
                      }`}
                      alt={u?.avatar?.name}
                    />
                  </div>
                  <div className='w-full'>
                    <div className='flex items-center justify-between gap-4'>
                      <h2
                        className='cursor-pointer text-lg font-medium'
                        onClick={() => navigate(`/profile/${u?._id}`)}
                      >
                        {u?.username}
                      </h2>
                      <button
                        className='bg-blue-500 text-neutral-100 px-4 py-1 rounded'
                        onClick={() => setVisibleModal({ visibleChatModal: u })}
                      >
                        Message
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
          {usersData?.totalPage > 1 && (
            <Pagination
              curPage={searchParams.get('page') || 1}
              totalPage={usersData?.totalPage}
            />
          )}
        </div>
      )}
      {isSuccessUsers && usersData?.users?.length === 0 && (
        <div className='my-8'>
          <p className='text-xl font-bold text-center'>No User Yet!</p>
        </div>
      )}
    </div>
  );
}

export default Users;
