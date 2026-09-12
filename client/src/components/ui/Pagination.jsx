import { useCallback } from 'react';
import ReactPaginate from 'react-paginate';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa6';
import { useTranslation } from 'react-i18next';
import useQueryString from '../../hooks/useQueryString';

/**
 * Phân trang.
 *
 * Phần lớn kiểu dáng nằm ở `.fu-pagination` trong index.css: react-paginate
 * dựng ra <li><a>, mà class truyền vào chỉ tới được <li> — muốn vùng bấm phủ
 * hết ô số thì phải nhắm vào thẻ <a> bên trong bằng CSS.
 *
 * Không vẽ gì khi chỉ có một trang.
 */
function Pagination({ curPage, totalPage }) {
  const { t } = useTranslation('common');
  const [createQueryString] = useQueryString();
  const handlePageClick = useCallback(
    (selectedItem) => createQueryString('page', selectedItem.selected + 1),
    [createQueryString]
  );

  if (!totalPage || totalPage <= 1) return null;

  return (
    <nav className='mt-6 flex justify-center' aria-label={t('pagination.page')}>
      <ReactPaginate
        forcePage={Number(curPage) - 1}
        className='fu-pagination flex list-none items-center gap-1'
        onPageChange={handlePageClick}
        pageCount={totalPage}
        pageRangeDisplayed={2}
        marginPagesDisplayed={1}
        previousLabel={
          <span className='flex items-center gap-1.5'>
            <FaChevronLeft className='size-3' aria-hidden='true' />
            <span className='hidden sm:inline'>{t('actions.previous')}</span>
          </span>
        }
        nextLabel={
          <span className='flex items-center gap-1.5'>
            <span className='hidden sm:inline'>{t('actions.next')}</span>
            <FaChevronRight className='size-3' aria-hidden='true' />
          </span>
        }
        breakLabel='…'
        activeClassName='fu-page-active'
        disabledClassName='fu-page-disabled'
        renderOnZeroPageCount={null}
      />
    </nav>
  );
}

export default Pagination;
