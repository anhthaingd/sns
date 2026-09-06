/**
 * Biểu đồ cột ngang bằng SVG/CSS thuần.
 *
 * Không thêm thư viện chart cho ba biểu đồ đơn giản: 200KB dependency cho thứ
 * vẽ được bằng vài chục dòng là không đáng, và thư viện chart là loại phụ
 * thuộc mục nhanh nhất.
 *
 * `rows`: [{ label, value, caption }]
 */
function BarChart({ rows, emptyLabel }) {
  if (!rows?.length) return <p>{emptyLabel}</p>;
  const max = Math.max(...rows.map((r) => r.value), 1);

  return (
    <ul className='flex flex-col gap-2'>
      {rows.map((r) => (
        <li key={r.label} className='flex items-center gap-3'>
          <span className='w-28 md:w-40 shrink-0 truncate text-sm' title={r.label}>
            {r.label}
          </span>
          <span className='flex-1 h-5 bg-neutral-200 dark:bg-neutral-700 rounded overflow-hidden'>
            <span
              className='block h-full bg-blue-500'
              style={{ width: `${(r.value / max) * 100}%` }}
            />
          </span>
          <span className='w-44 shrink-0 text-sm text-right text-neutral-500'>
            {r.caption}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default BarChart;
