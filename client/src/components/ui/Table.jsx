import { useMemo } from 'react';
import cn from '../../services/utils/cn';
import Pagination from './Pagination';

/**
 * Bảng dữ liệu cho các trang quản trị.
 *
 * Điểm khác bản cũ:
 *   - Hàng tiêu đề DÍNH khi cuộn dọc, nên cuộn tới hàng thứ 40 vẫn biết cột nào
 *     là cột nào.
 *   - Chỉ có đường kẻ NGANG giữa các hàng. Kẻ ô đầy đủ làm mắt phải nhảy qua
 *     lưới mới đọc được một dòng.
 *   - Phần phân trang dùng chung component `Pagination`, thay vì cấu hình
 *     react-paginate lần thứ hai với kiểu dáng khác hẳn.
 */
const Table = ({ tHeader, renderedData, totalPage, currPage, customClass }) => {
  const tdHeader = useMemo(
    () =>
      tHeader.map((h, index) => (
        <th
          key={index}
          scope='col'
          className='whitespace-nowrap px-4 py-3 text-left text-2xs font-bold uppercase tracking-wider text-fg-subtle'
        >
          {h}
        </th>
      )),
    [tHeader]
  );

  return (
    <div className='overflow-hidden rounded-card bg-surface ring-1 ring-inset ring-line'>
      <div className='max-h-[70vh] overflow-auto'>
        <table className={cn('w-full text-sm', customClass)}>
          <thead className='sticky top-0 z-10 bg-surface-2 shadow-[0_1px_0_rgb(var(--fu-line))]'>
            <tr>{tdHeader}</tr>
          </thead>
          <tbody className='divide-y divide-line [&>tr:hover]:bg-surface-2'>
            {renderedData}
          </tbody>
        </table>
      </div>
      {currPage && totalPage > 1 && (
        <div className='border-t border-line px-2 pb-2'>
          <Pagination curPage={currPage} totalPage={totalPage} />
        </div>
      )}
    </div>
  );
};

export default Table;
