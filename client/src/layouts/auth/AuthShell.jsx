import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { FaBriefcase, FaChartSimple, FaUserGroup } from 'react-icons/fa6';
import { getWebInfo } from '../../services/redux/slice/userSlice';
import LanguageSwitcher from '../../components/common/LanguageSwitcher';
import mediaUrl from '../../services/utils/media';

const POINTS = [
  { icon: FaBriefcase, key: 'brand.points.jobs' },
  { icon: FaChartSimple, key: 'brand.points.gap' },
  { icon: FaUserGroup, key: 'brand.points.social' },
];

/**
 * Khung chung của hai trang đăng nhập / đăng ký.
 *
 * Bản cũ đặt cả trang ở `position: absolute` với `h-4/5`, nên form đăng ký dài
 * hơn khung là bị cắt cụt — trên laptop 13" không cuộn tới được nút "Đăng ký".
 * Ở đây khung cao tối thiểu bằng màn hình và cuộn bình thường.
 *
 * Bảng bên trái thay hai tấm ảnh stock bằng nền chuyển màu chàm → asagi phủ
 * hoa văn sóng seigaiha: nhẹ hơn vài trăm KB và nói đúng câu chuyện của sản
 * phẩm hơn một bức ảnh văn phòng bất kỳ.
 *
 * @param quote câu trích lấy từ cấu hình website (khác nhau giữa hai trang)
 */
function AuthShell({ title, quote, children }) {
  const { t } = useTranslation('auth');
  const webInfo = useSelector(getWebInfo);
  const logo = mediaUrl(webInfo?.logo);
  const name = webInfo?.website_name || 'Fuurin';

  return (
    <div className='flex min-h-screen bg-bg'>
      {/* Bảng nhãn hiệu — ẩn dưới lg để form được trọn chiều ngang */}
      <section className='relative hidden w-[44%] max-w-xl shrink-0 overflow-hidden bg-ai-800 lg:flex lg:flex-col lg:justify-between'>
        <div
          className='absolute inset-0 bg-gradient-to-br from-ai-700 via-ai-800 to-asagi-800'
          aria-hidden='true'
        />
        <div
          className='fu-seigaiha absolute inset-0 text-white opacity-[0.09]'
          aria-hidden='true'
        />

        <div className='relative flex items-center gap-3 p-10'>
          <img
            className='size-9'
            src={logo || '/fuurin.svg'}
            alt=''
          />
          <span className='font-display text-xl font-black tracking-tight text-white'>
            {name}
          </span>
        </div>

        <div className='relative px-10'>
          <h2 className='font-display text-4xl font-black leading-tight text-white'>
            {t('brand.tagline')}
          </h2>
          <ul className='mt-8 flex flex-col gap-4'>
            {POINTS.map(({ icon: Icon, key }) => (
              <li key={key} className='flex items-center gap-3 text-white/85'>
                <span className='flex size-9 shrink-0 items-center justify-center rounded-full bg-white/10 text-asagi-200'>
                  <Icon className='size-4' aria-hidden='true' />
                </span>
                <span className='text-sm leading-snug'>{t(key)}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className='relative p-10'>
          {quote && (
            <blockquote className='border-l-2 border-asagi-300 pl-4 text-sm italic leading-relaxed text-white/70'>
              {quote}
            </blockquote>
          )}
        </div>
      </section>

      {/* Cột form */}
      <section className='flex min-w-0 flex-1 flex-col'>
        <div className='flex items-center justify-between gap-4 p-4 sm:p-6'>
          <div className='flex items-center gap-2 lg:invisible'>
            <img className='size-7' src={logo || '/fuurin.svg'} alt='' />
            <span className='font-display text-base font-black text-brand-text'>
              {name}
            </span>
          </div>
          <LanguageSwitcher />
        </div>

        <div className='flex flex-1 items-center justify-center px-4 pb-10 sm:px-6'>
          <div className='w-full max-w-sm'>
            <h1 className='font-display text-3xl font-black tracking-tight text-fg'>
              {title}
            </h1>
            <div className='mt-6'>{children}</div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AuthShell;
