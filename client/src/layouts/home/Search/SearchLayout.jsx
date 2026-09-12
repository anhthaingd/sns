import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaMagnifyingGlass } from 'react-icons/fa6';
import Page from '../../Page';
import Tabs from '../../../components/ui/Tabs';
import Button from '../../../components/ui/Button';
import EmptyState from '../../../components/ui/EmptyState';
import SectionHeading from '../../../components/ui/SectionHeading';
import useQueryString from '../../../hooks/useQueryString';

const Users = lazy(() => import('./components/Users'));
const Posts = lazy(() => import('./components/Posts'));

function SearchLayout() {
  const { t } = useTranslation(['user', 'post', 'common']);
  const [searchParams] = useSearchParams();
  const [createQueryString, deleteQueryString] = useQueryString();
  const curTab = searchParams.get('tab') || 'users';
  const term = searchParams.get('s');
  const [searchValue, setSearchValue] = useState(term || '');

  // Thanh trên cùng điều hướng sang /search?s=... — nếu ô nhập không đọc lại
  // tham số đó thì người dùng thấy kết quả cho một từ khoá mà ô tìm kiếm để
  // trống, và gõ tiếp một chữ là mất luôn từ khoá cũ.
  useEffect(() => setSearchValue(term || ''), [term]);

  const handleSearch = () => {
    if (searchValue !== '') createQueryString('s', searchValue);
    else deleteQueryString();
  };

  const tabs = useMemo(
    () => [
      { key: 'users', label: t('search.people') },
      { key: 'posts', label: t('post:plural') },
    ],
    [t]
  );

  return (
    <Page rail={false}>
      <SectionHeading title={t('search.title')} />

      <form
        className='mt-5 flex gap-2'
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
      >
        <div className='relative min-w-0 flex-1'>
          <FaMagnifyingGlass
            className='pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-fg-subtle'
            aria-hidden='true'
          />
          <input
            autoFocus
            className='h-12 w-full rounded-xl bg-surface pl-11 pr-4 text-base text-fg ring-1 ring-inset ring-line transition-shadow placeholder:text-fg-subtle focus:ring-2 focus:ring-accent'
            type='search'
            placeholder={t('search.placeholder')}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </div>
        <Button type='submit' size='lg'>
          {t('common:actions.search')}
        </Button>
      </form>

      <Tabs
        className='mt-6'
        items={tabs}
        value={curTab}
        onChange={(key) => createQueryString('tab', key)}
      />

      <div className='mt-6'>
        <Suspense fallback={null}>
          {term ? (
            <>
              {curTab === 'users' && <Users searchValue={term} />}
              {curTab === 'posts' && <Posts searchValue={term} />}
            </>
          ) : (
            <EmptyState icon={FaMagnifyingGlass} title={t('search.placeholder')} />
          )}
        </Suspense>
      </div>
    </Page>
  );
}

export default SearchLayout;
