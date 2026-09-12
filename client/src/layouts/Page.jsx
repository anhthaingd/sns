import cn from '../services/utils/cn';
import LeftAside from './components/LeftAside';
import RightAside from './components/RightAside';
import MobileNav from './components/MobileNav';

/**
 * Khung ba cột của toàn ứng dụng.
 *
 * Bản cũ định vị hai cột bên bằng `position: fixed` rồi chừa chỗ cho chúng
 * bằng `pl-[360px] pr-[330px]` cứng trên khung giữa. Hai con số đó không đổi
 * theo breakpoint, nên dưới 1024px — nơi cả hai cột đã bị ẩn — nội dung vẫn bị
 * đẩy vào giữa một khoảng trống 690px.
 *
 * Giờ là lưới CSS: cột nào không hiển thị thì rãnh của nó biến mất theo. Ba mốc:
 *   < lg   một cột, điều hướng nằm ở thanh dưới đáy
 *   lg     thêm cột menu trái
 *   xl     thêm cột danh bạ phải
 *
 * @param wide bỏ giới hạn bề ngang của khung nội dung — cho trang bảng biểu
 *             (quản trị, bản đồ thị trường) cần hết chiều ngang
 * @param rail đặt false ở những trang đã có cột bộ lọc riêng (việc làm, match):
 *             ba cột nội dung cạnh nhau thì cột nào cũng hẹp đến mức vô dụng
 */
function Page({ children, wide = false, rail = true, className }) {
  return (
    <div className='min-h-screen bg-bg'>
      <div
        className={cn(
          'mx-auto grid max-w-shell grid-cols-1 lg:grid-cols-[theme(spacing.nav)_minmax(0,1fr)]',
          rail && 'xl:grid-cols-[theme(spacing.nav)_minmax(0,1fr)_theme(spacing.rail)]'
        )}
      >
        <LeftAside />

        <main
          id='fu-main'
          className={cn(
            'min-w-0 px-4 pb-24 pt-5 sm:px-6 lg:pb-10',
            !wide && 'mx-auto w-full max-w-5xl',
            className
          )}
        >
          {children}
        </main>

        {rail && <RightAside />}
      </div>

      <MobileNav />
    </div>
  );
}

export default Page;
