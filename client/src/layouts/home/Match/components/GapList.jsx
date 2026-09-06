import { FaCircleCheck, FaTriangleExclamation, FaCircleInfo } from 'react-icons/fa6';

/**
 * Danh sách "còn thiếu gì".
 *
 * Tách rõ điều kiện LOẠI (blocking) với điểm nên có: người dùng cần biết cái
 * nào bắt buộc phải bù mới nộp được, cái nào chỉ là điểm cộng.
 */
function GapList({ gaps = [], met = [] }) {
  const blocking = gaps.filter((g) => g.blocking);
  const optional = gaps.filter((g) => !g.blocking);

  return (
    <div className='flex flex-col gap-4'>
      {blocking.length > 0 && (
        <section>
          <h4 className='font-bold text-rose-600 dark:text-rose-400 flex items-center gap-2 mb-2'>
            <FaTriangleExclamation /> Bắt buộc phải bù ({blocking.length})
          </h4>
          <ul className='flex flex-col gap-2'>
            {blocking.map((g, i) => (
              <li
                key={`${g.kind}-${i}`}
                className='p-3 rounded border-l-4 border-rose-500 bg-rose-50 dark:bg-rose-950 text-sm'
              >
                {g.message}
              </li>
            ))}
          </ul>
        </section>
      )}

      {optional.length > 0 && (
        <section>
          <h4 className='font-bold text-amber-600 dark:text-amber-400 flex items-center gap-2 mb-2'>
            <FaCircleInfo /> Nên có thêm ({optional.length})
          </h4>
          <ul className='flex flex-col gap-2'>
            {optional.map((g, i) => (
              <li
                key={`${g.kind}-${i}`}
                className='p-3 rounded border-l-4 border-amber-500 bg-amber-50 dark:bg-amber-950 text-sm'
              >
                {g.message}
              </li>
            ))}
          </ul>
        </section>
      )}

      {met.length > 0 && (
        <section>
          <h4 className='font-bold text-green-600 dark:text-green-400 flex items-center gap-2 mb-2'>
            <FaCircleCheck /> Bạn đã đáp ứng ({met.length})
          </h4>
          <ul className='flex flex-col gap-2'>
            {met.map((m, i) => (
              <li
                key={i}
                className='p-3 rounded border-l-4 border-green-500 bg-green-50 dark:bg-green-950 text-sm'
              >
                {m}
              </li>
            ))}
          </ul>
        </section>
      )}

      {blocking.length === 0 && optional.length === 0 && met.length === 0 && (
        <p className='text-sm opacity-70'>
          Tin này không nêu yêu cầu cụ thể nào để đối chiếu với CV của bạn.
        </p>
      )}
    </div>
  );
}

export default GapList;
