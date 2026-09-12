import {
  FaHouse,
  FaMagnifyingGlass,
  FaLayerGroup,
  FaBookmark,
  FaBriefcase,
  FaBullseye,
  FaArrowTrendUp,
  FaChartColumn,
  FaFileLines,
  FaUser,
  FaGear,
  FaShieldHalved,
} from 'react-icons/fa6';

/**
 * Một nguồn sự thật duy nhất cho điều hướng.
 *
 * Cột trái trên desktop, ngăn kéo và thanh dưới trên mobile đều đọc từ đây,
 * nên thêm một trang là sửa một chỗ. Trước đây mỗi mục là một khối <button>
 * chép tay trong LeftAside, và ba mục khác nhau vô tình dùng chung một biểu
 * tượng vì không ai để ý.
 *
 * `end: true` cho những đường dẫn là tiền tố của đường dẫn khác ("/" là tiền
 * tố của tất cả, "/match" là tiền tố của "/match/whatif") — thiếu nó thì hai
 * mục cùng sáng một lúc.
 */
export function buildNavGroups(user) {
  const isAdmin = user?.role?.value === 1;
  const profilePath = `/profile/${user?._id ?? ''}`;

  return [
    {
      id: 'discover',
      labelKey: 'groups.discover',
      items: [
        { to: '/', labelKey: 'home', icon: FaHouse, end: true },
        { to: '/channels', labelKey: 'channels', icon: FaLayerGroup },
        { to: '/search', labelKey: 'search', icon: FaMagnifyingGlass },
        { to: '/bookmarks', labelKey: 'bookmark', icon: FaBookmark },
      ],
    },
    {
      id: 'career',
      labelKey: 'groups.career',
      items: [
        { to: '/recruitment', labelKey: 'recruitment', icon: FaBriefcase },
        { to: '/match', labelKey: 'match', icon: FaBullseye, end: true },
        { to: '/match/whatif', labelKey: 'whatif', icon: FaArrowTrendUp },
        { to: '/market', labelKey: 'market', icon: FaChartColumn },
        { to: '/resume', labelKey: 'resume', icon: FaFileLines },
      ],
    },
    {
      id: 'account',
      labelKey: 'groups.account',
      items: [
        { to: profilePath, labelKey: 'profile', icon: FaUser },
        {
          to: isAdmin ? '/admin/settings' : '/users/settings',
          labelKey: 'settings',
          icon: FaGear,
        },
        ...(isAdmin
          ? [{ to: '/admin/management', labelKey: 'management', icon: FaShieldHalved }]
          : []),
      ],
    },
  ];
}

/**
 * Bốn mục cho thanh điều hướng dưới cùng trên điện thoại.
 *
 * Cố ý chỉ bốn: mục thứ năm là nút "Thêm" mở ngăn kéo chứa toàn bộ menu. Nhét
 * đủ mười hai mục vào thanh dưới thì mỗi ô rộng 30px, không bấm trúng được.
 *
 * Dùng nhãn NGẮN (`short.*`) chứ không dùng nhãn của menu đầy đủ: mỗi ô rộng
 * khoảng 78px trên iPhone, mà "Công ty phù hợp" cần gấp đôi chỗ đó.
 */
export const MOBILE_NAV = [
  { to: '/', labelKey: 'short.home', icon: FaHouse, end: true },
  { to: '/recruitment', labelKey: 'short.recruitment', icon: FaBriefcase },
  { to: '/match', labelKey: 'short.match', icon: FaBullseye, end: true },
  { to: '/channels', labelKey: 'short.channels', icon: FaLayerGroup },
];
