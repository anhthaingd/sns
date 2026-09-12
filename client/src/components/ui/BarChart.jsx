import cn from '../../services/utils/cn';

/**
 * Biểu đồ cột ngang bằng HTML/CSS thuần.
 *
 * Không thêm thư viện chart cho ba biểu đồ đơn giản: 200KB dependency cho thứ
 * vẽ được bằng vài chục dòng là không đáng, và thư viện chart là loại phụ
 * thuộc mục nhanh nhất.
 *
 * Quy ước vẽ:
 *   - MỘT chuỗi số liệu duy nhất (số tin tuyển dụng) nên dùng MỘT màu — asagi.
 *     Tô mỗi cột một màu khác nhau sẽ ngụ ý các hàng thuộc những loại khác
 *     nhau, trong khi chúng chỉ khác nhau ở độ lớn.
 *   - Cột mảnh (10px) trên rãnh nền mờ: phần mực dày nhất phải là dữ liệu,
 *     không phải khung. Bản cũ dùng cột cao 20px nền xám đậm, nhìn xa thành
 *     một khối xám liền.
 *   - Con số nằm trong chú thích bên phải chứ không lặp lại trên cột.
 *
 * Độ tương phản của màu cột so với nền: 5.9:1 (sáng) và 5.7:1 (tối).
 *
 * `rows`: [{ label, value, caption }]
 */
function BarChart({ rows, emptyLabel }) {
  if (!rows?.length) return <p className='text-sm text-fg-muted'>{emptyLabel}</p>;
  const max = Math.max(...rows.map((r) => r.value), 1);

  return (
    <ul className='flex flex-col'>
      {rows.map((r) => (
        <li
          key={r.label}
          className={cn(
            'group grid items-center gap-x-3 gap-y-1 rounded-lg px-2 py-2 transition-colors hover:bg-surface-2',
            'grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] sm:grid-cols-[minmax(0,10rem)_minmax(0,1fr)_auto]'
          )}
        >
          <span className='truncate text-sm font-medium text-fg' title={r.label}>
            {r.label}
          </span>

          <span
            className='h-2.5 w-full overflow-hidden rounded-pill bg-surface-2 group-hover:bg-surface-3'
            role='presentation'
          >
            <span
              className='block h-full rounded-pill bg-accent transition-[width] duration-500 ease-out'
              style={{ width: `${Math.max((r.value / max) * 100, 1.5)}%` }}
            />
          </span>

          {/* Chú thích mang cả cỡ mẫu lẫn trung vị, nên nó vừa là nhãn giá trị
              vừa là phần "đọc được bằng chữ" thay cho việc rê chuột. */}
          <span className='tnum col-span-2 text-xs text-fg-subtle sm:col-span-1 sm:text-right'>
            {r.caption}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default BarChart;
