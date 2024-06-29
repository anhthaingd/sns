import React from 'react';

function NotFoundItem({ message }) {
  return (
    <section className='w-full h-full rounded-lg border border-neutral-300 dark:border-neutral-700 overflow-x-auto p-8 flex flex-col items-center'>
      <p className='font-bold text-neutral-700 dark:text-neutral-100'>
        {message}
      </p>
    </section>
  );
}

export default NotFoundItem;
