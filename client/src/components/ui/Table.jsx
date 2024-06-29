import React, { useCallback, useMemo } from 'react';
import ReactPaginate from 'react-paginate';
import { TbChevronLeft, TbChevronRight } from 'react-icons/tb';
import useQueryString from '../../hooks/useQueryString';
const Table = ({ tHeader, renderedData, totalPage, currPage, customClass }) => {
  const [createQueryString] = useQueryString();
  const handlePageClick = useCallback(
    (selectedItem) => {
      createQueryString('page', selectedItem.selected + 1);
    },
    [createQueryString]
  );
  const tdHeader = useMemo(() => {
    return tHeader.map((h, index) => {
      return (
        <td key={index} className='p-4'>
          {h}
        </td>
      );
    });
  }, [tHeader]);
  return (
    <div className='w-full rounded-lg border border-neutral-300 dark:border-neutral-700 overflow-x-auto overflow-y-auto'>
      <table
        className={`relative w-full h-full whitespace-nowrap ${
          customClass ? customClass : ''
        }`}
      >
        <thead className='text-xs font-semibold tracking-wide text-left text-neutral-700 dark:text-neutral-100 uppercase border-b border-neutral-300 dark:border-neutral-700'>
          <tr className='text-center font-bold uppercase'>{tdHeader}</tr>
        </thead>
        <tbody>{renderedData}</tbody>
      </table>
      {currPage && totalPage && totalPage > 1 && (
        <ReactPaginate
          forcePage={Number(currPage) - 1}
          className='my-2 mx-4 flex justify-end items-center gap-[10px] font-bold text-neutral-700 dark:text-neutral-100 py-2'
          nextLabel={
            <TbChevronRight className='text-neutral-700 dark:text-neutral-100' />
          }
          onPageChange={handlePageClick}
          pageRangeDisplayed={2}
          marginPagesDisplayed={2}
          pageCount={totalPage}
          previousLabel={
            <TbChevronLeft className='text-neutral-700 dark:text-neutral-100' />
          }
          pageClassName='text-sm w-[32px] h-[32px] flex justify-center items-center cursor-pointer'
          pageLinkClassName='w-full h-full flex justify-center items-center'
          nextClassName='text-neutral-700 dark:text-neutral-100'
          breakLabel='...'
          breakClassName='page-item'
          containerClassName='pagination'
          activeClassName='bg-neutral-700 dark:bg-neutral-200 rounded-[4px] dark:text-neutral-700 text-neutral-100'
          renderOnZeroPageCount={null}
        />
      )}
    </div>
  );
};

export default Table;
