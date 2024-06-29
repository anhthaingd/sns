import React from 'react';
import LeftAside from './components/LeftAside';
import RightAside from './components/RightAside';

function Page({ children }) {
  return (
    <main className='min-h-[100vh] py-[72px] text-sm md:text-base text-neutral-700 dark:text-neutral-300 dark:bg-neutral-900 flex-1'>
      <LeftAside />
      <section className='pl-[360px] pr-[330px] rounded py-4'>
        {children}
      </section>
      <RightAside />
    </main>
  );
}

export default Page;
