import { useState } from 'react';
import {
  FaCircleCheck,
  FaTriangleExclamation,
  FaCircleInfo,
} from 'react-icons/fa6';
import { useTranslation } from 'react-i18next';
import { gapText, metText } from '../../../../services/utils/matchText';
import cn from '../../../../services/utils/cn';

/**
 * Ba nhóm dùng ba màu cố định của hệ thống, giống hệt ngưỡng của đồng hồ điểm
 * khớp: đỏ son = điều kiện loại, vàng yamabuki = điểm cộng còn thiếu, xanh
 * matcha = đã đạt. Nhờ vậy một màu luôn nói cùng một điều trên mọi màn hình.
 */
const GROUPS = {
  blocking: {
    icon: FaTriangleExclamation,
    head: 'text-danger-text',
    item: 'border-danger bg-danger-soft',
  },
  optional: {
    icon: FaCircleInfo,
    head: 'text-warning-text',
    item: 'border-warning bg-warning-soft',
  },
  met: {
    icon: FaCircleCheck,
    head: 'text-success-text',
    item: 'border-success bg-success-soft',
  },
};

/**
 * Số mục hiện ra trước khi phải bấm "xem thêm".
 *
 * Ở mức một tin tuyển dụng, danh sách hiếm khi quá 6 mục nên ngưỡng này không
 * bao giờ chạm tới. Nó tồn tại cho mức CÔNG TY: một công ty đang tuyển cả trăm
 * vị trí có thể đòi vài chục kỹ năng mà CV chưa có. Danh sách đã xếp theo số vị
 * trí yêu cầu giảm dần, nên mười hai dòng đầu chính là phần đáng đọc nhất.
 */
const VISIBLE = 12;

function GapGroup({ kind, title, items, render }) {
  const { t } = useTranslation('match');
  const [expanded, setExpanded] = useState(false);
  if (!items.length) return null;
  const { icon: Icon, head, item } = GROUPS[kind];
  const shown = expanded ? items : items.slice(0, VISIBLE);
  const hidden = items.length - shown.length;

  return (
    <section>
      <h4 className={cn('mb-2 flex items-center gap-2 text-sm font-bold', head)}>
        <Icon className='size-3.5' aria-hidden='true' />
        {title}
      </h4>
      <ul className='flex flex-col gap-2'>
        {shown.map((entry, i) => (
          <li
            key={`${entry.kind || kind}-${i}`}
            className={cn('rounded-lg border-l-[3px] p-3 text-sm text-fg', item)}
          >
            {render(entry)}
          </li>
        ))}
      </ul>
      {(hidden > 0 || expanded) && (
        <button
          type='button'
          className='mt-2 text-sm font-semibold text-accent-text hover:underline'
          onClick={() => setExpanded((prev) => !prev)}
        >
          {expanded ? t('gapList.showLess') : t('gapList.showMore', { count: hidden })}
        </button>
      )}
    </section>
  );
}

/**
 * Danh sách "còn thiếu gì".
 *
 * Tách rõ điều kiện LOẠI (blocking) với điểm nên có: người dùng cần biết cái
 * nào bắt buộc phải bù mới nộp được, cái nào chỉ là điểm cộng.
 */
function GapList({ gaps = [], met = [] }) {
  const { t } = useTranslation('match');
  const blocking = gaps.filter((g) => g.blocking);
  const optional = gaps.filter((g) => !g.blocking);

  if (!blocking.length && !optional.length && !met.length) {
    return <p className='text-sm text-fg-muted'>{t('gapList.noRequirement')}</p>;
  }

  return (
    <div className='flex flex-col gap-5'>
      <GapGroup
        kind='blocking'
        title={t('gapList.blocking', { count: blocking.length })}
        items={blocking}
        render={(g) => gapText(t, g)}
      />
      <GapGroup
        kind='optional'
        title={t('gapList.optional', { count: optional.length })}
        items={optional}
        render={(g) => gapText(t, g)}
      />
      <GapGroup
        kind='met'
        title={t('gapList.met', { count: met.length })}
        items={met}
        render={(m) => metText(t, m)}
      />
    </div>
  );
}

export default GapList;
