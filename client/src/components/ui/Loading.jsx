import React from 'react';
const Loading = React.memo(() => {
  const loadingItems = [];
  for (let i = 0; i < 3; i++) {
    loadingItems.push(<div key={i} className='circle'></div>);
  }
  return <main className='loading dark:bg-neutral-900'>{loadingItems}</main>;
});

export default Loading;
