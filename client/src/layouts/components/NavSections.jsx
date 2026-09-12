import { useTranslation } from 'react-i18next';
import { buildNavGroups } from './navItems';
import NavLinkItem from './NavLinkItem';

/**
 * Danh sách menu đã chia nhóm. Dùng chung cho cột trái (desktop) và ngăn kéo
 * (mobile), nên hai nơi không thể lệch nhau.
 */
function NavSections({ user, onNavigate }) {
  const { t } = useTranslation('nav');

  return (
    <nav className='flex flex-col gap-5'>
      {buildNavGroups(user).map((group) => (
        <div key={group.id}>
          <h2 className='mb-1.5 px-3.5 text-2xs font-bold uppercase tracking-wider text-fg-subtle'>
            {t(group.labelKey)}
          </h2>
          <div className='flex flex-col gap-0.5'>
            {group.items.map((item) => (
              <NavLinkItem
                key={item.to + item.labelKey}
                to={item.to}
                end={item.end}
                icon={item.icon}
                label={t(item.labelKey)}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        </div>
      ))}
    </nav>
  );
}

export default NavSections;
