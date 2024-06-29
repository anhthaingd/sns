import React, { Suspense, lazy, useState } from 'react';
import Page from '../../Page';
// import Jobsinjapan from './components/Jobsinjapan';
const LinkedJob = lazy(() => import('./components/LinkedJob'));
const NihongoJob = lazy(() => import('./components/NihongoJob'));
const GaijinpotJob = lazy(() => import('./components/GaijinpotJob'));
const DaiJob = lazy(() => import('./components/DaiJob'));
function RecruitmentLayout() {
  const [curTab, setCurTab] = useState('linked');

  return (
    <Page>
      <section className='mb-8'>
        <div className='flex items-center gap-8 text-lg bg-neutral-100 dark:bg-neutral-800 p-4 rounded font-bold'>
          <button
            className={`${curTab === 'linked' ? 'text-blue-500' : ''}`}
            onClick={() => setCurTab('linked')}
          >
            Linked
          </button>
          <button
            className={`${curTab === 'nihongo' ? 'text-blue-500' : ''}`}
            onClick={() => setCurTab('nihongo')}
          >
            Nihongo
          </button>
          <button
            className={`${curTab === 'gaijinpot' ? 'text-blue-500' : ''}`}
            onClick={() => setCurTab('gaijinpot')}
          >
            Gaijinpot
          </button>
          {/* <button
            className={`${curTab === 'jobsinjapan' ? 'text-blue-500' : ''}`}
            onClick={() => setCurTab('jobsinjapan')}
          >
            Jobsinjapan
          </button> */}
          <button
            className={`${curTab === 'daijob' ? 'text-blue-500' : ''}`}
            onClick={() => setCurTab('daijob')}
          >
            DaiJob
          </button>
        </div>
      </section>
      <section>
        <Suspense>
          {curTab === 'linked' && <LinkedJob />}
          {curTab === 'nihongo' && <NihongoJob />}
          {curTab === 'gaijinpot' && <GaijinpotJob />}
          {/* {curTab === 'jobsinjapan' && <Jobsinjapan />} */}
          {curTab === 'daijob' && <DaiJob />}
        </Suspense>
      </section>
    </Page>
  );
}

export default RecruitmentLayout;
