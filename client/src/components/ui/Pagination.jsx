import React, { useCallback } from 'react';
import ReactPaginate from 'react-paginate';
import { FaAnglesLeft, FaAnglesRight } from 'react-icons/fa6';
import useQueryString from '../../hooks/useQueryString';

function Pagination({ curPage, totalPage }) {
  const [createQueryString] = useQueryString();
  const handlePageClick = useCallback(
    (selectedItem) => {
      createQueryString('page', selectedItem.selected + 1);
    },
    [createQueryString]
  );
  return (
    <ReactPaginate
      forcePage={Number(curPage) - 1}
      className='my-2 mx-4 flex justify-center items-stretch gap-[10px] font-bold text-neutral-700 dark:text-neutral-100 py-2'
      nextLabel={
        <button className='flex items-center gap-2 px-4 border border-neutral-300 py-2 text-neutral-500 dark:text-neutral-100 text-sm'>
          <p>Next</p>
          <FaAnglesRight />
        </button>
      }
      onPageChange={handlePageClick}
      pageRangeDisplayed={2}
      marginPagesDisplayed={2}
      pageCount={totalPage}
      previousLabel={
        <button className='flex items-center gap-2 px-4 border border-neutral-300 py-2 text-neutral-500 dark:text-neutral-100 text-sm'>
          <FaAnglesLeft />
          <p>Previous</p>
        </button>
      }
      pageClassName='py-2 px-4 border border-neutral-300 text-sm flex justify-center items-center cursor-pointer'
      // pageLinkClassName='py-2 w-full h-full flex justify-center items-center'
      nextClassName='text-neutral-700'
      breakLabel='...'
      breakClassName='page-item'
      containerClassName='pagination'
      activeClassName='bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-700 text-white'
      renderOnZeroPageCount={null}
    />
  );
}

export default Pagination;
