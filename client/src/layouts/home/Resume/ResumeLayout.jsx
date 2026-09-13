import { useCallback, useContext, useEffect, useState } from 'react';
import Page from '../../Page';
import {
  FaCakeCandles,
  FaEnvelope,
  FaLocationDot,
  FaPhone,
  FaGithub,
  FaXmark,
} from 'react-icons/fa6';
import ResumeModal from '../../../components/modal/resume/ResumeModal';
import ImageUpload from '../../../components/ui/ImageUpload';
import {
  useGetResumeAdviceQuery,
  useGetResumeQuery,
  usePostResumeMutation,
} from '../../../services/redux/query/api/resumeApi';
import AdviceCard from '../../../components/ui/AdviceCard';
import useAdviceLang from '../../../hooks/useAdviceLang';
import { ModalContext } from '../../../context/ModalProvider';
import useMutationToast from '../../../hooks/useMutationToast';
import { useTranslation } from 'react-i18next';

// Cung thang voi `LANGUAGE_LEVELS` o backend (app/models/job.py). Thu tu tu
// thap den cao, dung de sinh dropdown va de tang so khop dem duoc.
const LANGUAGE_LEVELS = [
  'none',
  'basic',
  'conversational',
  'business',
  'fluent',
  'native',
];

// Ô nhập của trang CV. Tách thành hằng số vì có gần ba mươi ô dùng chung đúng
// một bộ class; trước đây chuỗi đó được chép tay ở từng chỗ, nên chỉ cần một
// lần chép thiếu là có một ô lệch hẳn kiểu dáng so với các ô còn lại.
const fieldClass =
  'w-full rounded-lg bg-surface px-3 py-2 text-sm text-fg ring-1 ring-inset ring-line ' +
  'transition-shadow placeholder:text-fg-subtle hover:ring-line-strong focus:outline-none focus:ring-2 focus:ring-accent';

const buttonBase =
  'inline-flex select-none items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold ' +
  'transition-all duration-150 ease-out active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50';
const addButtonClass = `${buttonBase} bg-surface-2 text-fg hover:bg-surface-3`;
const previewButtonClass = `${buttonBase} bg-surface text-fg ring-1 ring-inset ring-line-strong hover:bg-surface-2`;
const saveButtonClass = `${buttonBase} bg-brand text-brand-on shadow-card hover:bg-brand-hover`;

function ResumeLayout() {
  const { t } = useTranslation(['resume', 'common']);
  const { state, setVisibleModal } = useContext(ModalContext);
  const { data: resumeData, isSuccess: isSuccessResume } = useGetResumeQuery();

  // Đây là nơi DUY NHẤT sửa được gốc rễ: CV ghi sơ sài thì vector kém và mọi
  // gợi ý phía sau kém theo, mà người dùng không hề biết.
  const lang = useAdviceLang();
  const advice = useGetResumeAdviceQuery({ lang }, { skip: !isSuccessResume });
  const [
    postResume,
    {
      data: postData,
      isSuccess: isSuccessPost,
      isLoading: isLoadingPost,
      isError: isErrorPost,
      error: errorPost,
    },
  ] = usePostResumeMutation();
  const [experience, setExperience] = useState({
    name: '',
    startTime: '',
    endTime: '',
    position: '',
    description: '',
  });
  const [skill, setSkill] = useState('');
  const [language, setLanguage] = useState('');
  const [project, setProject] = useState({
    name: '',
    tech: '',
    description: '',
  });
  const [certificate, setCertificate] = useState({
    name: '',
    certificate: null,
  });
  const [form, setForm] = useState({
    name: '',
    position: '',
    avatar: null,
    oldAvatar: null,
    birthday: '',
    email: '',
    address: '',
    phone: '',
    github: '',
    objective: '',
    educationName: '',
    educationMajor: '',
    educationCompletion: '',
    educationGPA: '',
    japaneseLevel: '',
    englishLevel: '',
    yearsOfExperience: '',
    desiredSalaryMin: '',
    desiredLocations: '',
    certificatesName: [],
    certificates: [],
    oldCertificates: [],
    editCertificates: [],
    experiences: [],
    skills: [],
    languages: [],
    projects: [],
  });
  useEffect(() => {
    if (isSuccessResume && resumeData) {
      if (resumeData.resume) {
        const resume = resumeData?.resume;
        setForm({
          name: resume.name,
          position: resume.position,
          avatar: null,
          oldAvatar: resume.avatar,
          birthday: resume.birthday,
          email: resume.email,
          address: resume.address,
          phone: resume.phone,
          github: resume.github,
          objective: resume.objective,
          educationName: resume.educationName,
          educationMajor: resume.educationMajor,
          educationCompletion: resume.educationCompletion,
          japaneseLevel: resume.japanese_level || '',
          englishLevel: resume.english_level || '',
          yearsOfExperience: resume.years_of_experience ?? '',
          desiredSalaryMin: resume.desired_salary_min ?? '',
          desiredLocations: (resume.desired_locations || []).join(', '),
          educationGPA: resume.educationGPA,
          certificatesName: [],
          certificates: [],
          oldCertificates: resume.certificates,
          editCertificates: resume.certificates,
          experiences: resume.experiences,
          skills: resume.skills,
          languages: resume.languages,
          projects: resume.projects,
        });
      }
    }
  }, [isSuccessResume, resumeData]);
  const handleAddExperience = useCallback(() => {
    setForm({ ...form, experiences: [...(form?.experiences || []), experience] });
    setExperience(() => {
      return { name: '', startTime: '', endTime: '' };
    });
  }, [experience, form]);
  const handleAddCertificate = useCallback(() => {
    if (!certificate.name || !certificate.certificate) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: t('validate.certificateIncomplete'),
        },
      });
    } else {
      setForm({
        ...form,
        certificates: [...form.certificates, certificate.certificate],
        certificatesName: [...form.certificatesName, certificate.name],
      });
      setCertificate(() => {
        return { name: '', certificate: null };
      });
    }
  }, [certificate, form, setVisibleModal, t]);
  const handleAddSkill = useCallback(() => {
    setForm({ ...form, skills: [...(form?.skills || []), skill] });
    setSkill(() => {
      return '';
    });
  }, [skill, form]);
  const handleAddLanguage = useCallback(() => {
    setForm({ ...form, languages: [...(form?.languages || []), language] });
    setLanguage(() => {
      return '';
    });
  }, [language, form]);
  const handleAddProject = useCallback(() => {
    setForm({ ...form, projects: [...(form?.projects || []), project] });
    setProject(() => {
      return { name: '', tech: '', description: '' };
    });
  }, [project, form]);
  const handlePostResume = useCallback(async () => {
    const formData = new FormData();
    formData.append('name', form.name);
    formData.append('position', form.position);
    formData.append('birthday', form.birthday);
    formData.append('email', form.email);
    formData.append('address', form.address);
    formData.append('phone', form.phone);
    formData.append('github', form.github);
    formData.append('objective', form.objective);
    formData.append('educationName', form.educationName);
    formData.append('educationMajor', form.educationMajor);
    formData.append('educationCompletion', form.educationCompletion);
    formData.append('skills', JSON.stringify(form.skills));
    formData.append('languages', JSON.stringify(form.languages));
    formData.append('projects', JSON.stringify(form.projects));
    formData.append('experiences', JSON.stringify(form.experiences));
    // Muc tieu nghe nghiep: de trong thi backend tu suy tu noi dung CV.
    formData.append('japaneseLevel', form.japaneseLevel);
    formData.append('englishLevel', form.englishLevel);
    formData.append('yearsOfExperience', form.yearsOfExperience);
    formData.append('desiredSalaryMin', form.desiredSalaryMin);
    formData.append(
      'desiredLocations',
      JSON.stringify(
        form.desiredLocations
          .split(',')
          .map((v) => v.trim())
          .filter(Boolean)
      )
    );
    if (form.oldAvatar) {
      formData.append('oldAvatar', JSON.stringify(form.oldAvatar));
    }
    if (form.avatar) {
      formData.append('avatar', form.avatar);
    }
    if (form.oldCertificates?.length > 0) {
      formData.append('oldCertificates', JSON.stringify(form.oldCertificates));
      formData.append(
        'editCertificates',
        JSON.stringify(form.editCertificates)
      );
    }
    if (form.certificates.length > 0) {
      formData.append(
        'certificatesName',
        JSON.stringify(form.certificatesName)
      );
      form.certificates.forEach((c) => {
        formData.append('certificates', c);
      });
    }
    await postResume(formData);
  }, [postData, form]);
  console.log(form.certificates);
  useMutationToast({
    data: postData,
    error: errorPost,
    isSuccess: isSuccessPost,
    isError: isErrorPost,
  });
  return (
    <Page>
      {state.visibleResumeModal && <ResumeModal />}
      <div className='flex flex-col gap-8' aria-disabled={isLoadingPost}>
        <div className='relative pl-3.5'>
          <span className='fu-cord' aria-hidden='true' />
          <h1 className='text-xl font-bold text-fg sm:text-2xl'>{t('title')}</h1>
        </div>

        <AdviceCard data={advice.data} isLoading={advice.isLoading} />
        <div className='flex flex-col gap-7 rounded-card bg-surface p-4 ring-1 ring-inset ring-line sm:p-6'>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.basicInfo')}</h2>
            {/* Ảnh trong CV Nhật là ảnh chân dung dọc, nên khung xem trước
                giữ đúng tỉ lệ 3:4 của ảnh chứng minh thư. */}
            <ImageUpload
              aspect='aspect-[3/4]'
              className='max-w-[15rem]'
              value={form.avatar}
              existing={form.oldAvatar}
              onChange={(file) => setForm((prev) => ({ ...prev, avatar: file }))}
              onRemove={() => setForm((prev) => ({ ...prev, avatar: null }))}
            />
            <input
              className={fieldClass}
              type='text'
              placeholder={t('field.fullName')}
              value={form?.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              className={fieldClass}
              type='text'
              placeholder={t('field.position')}
              value={form?.position}
              onChange={(e) => setForm({ ...form, position: e.target.value })}
            />
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.contact')}</h2>
            <div className='flex flex-col gap-4'>
              <div className='flex items-center gap-4'>
                <label
                  className='flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft text-accent-text'
                  htmlFor='date'
                >
                  <FaCakeCandles className='size-4' />
                </label>
                <input
                  className={fieldClass}
                  type='date'
                  required
                  value={form?.birthday}
                  onChange={(e) =>
                    setForm({ ...form, birthday: e.target.value })
                  }
                />
              </div>
              <div className='flex items-center gap-4'>
                <label
                  className='flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft text-accent-text'
                  htmlFor='email'
                >
                  <FaEnvelope className='size-4' />
                </label>
                <input
                  className={fieldClass}
                  type='email'
                  placeholder={t('field.email')}
                  required
                  value={form?.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div className='flex items-center gap-4'>
                <label
                  className='flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft text-accent-text'
                  htmlFor='address'
                >
                  <FaLocationDot className='size-4' />
                </label>
                <input
                  className={fieldClass}
                  type='text'
                  placeholder={t('field.address')}
                  value={form?.address}
                  onChange={(e) =>
                    setForm({ ...form, address: e.target.value })
                  }
                />
              </div>
              <div className='flex items-center gap-4'>
                <label
                  className='flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft text-accent-text'
                  htmlFor='phone'
                >
                  <FaPhone className='size-4' />
                </label>
                <input
                  className={fieldClass}
                  type='number'
                  placeholder={t('field.phone')}
                  value={form?.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </div>
              <div className='flex items-center gap-4'>
                <label
                  className='flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft text-accent-text'
                  htmlFor='github'
                >
                  <FaGithub className='size-4' />
                </label>
                <input
                  className={fieldClass}
                  placeholder={t('field.github')}
                  pattern='https://.*'
                  value={form?.github}
                  onChange={(e) => setForm({ ...form, github: e.target.value })}
                />
              </div>
            </div>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.objective')}</h2>
            <textarea
              className={fieldClass}
              placeholder={t('field.objective')}
              rows={3}
              value={form?.objective}
              onChange={(e) => setForm({ ...form, objective: e.target.value })}
            />
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.experience')}</h2>
            <div className='flex flex-col gap-4'>
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.company')}
                value={experience?.name}
                onChange={(e) =>
                  setExperience({ ...experience, name: e.target.value })
                }
              />
              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <label className='font-medium' htmlFor='start_time'>{t('field.startTimeLabel')}</label>
                  <input
                    className={fieldClass}
                    type='text'
                    placeholder={t('field.startTime')}
                    value={experience?.startTime}
                    onChange={(e) =>
                      setExperience({
                        ...experience,
                        startTime: e.target.value,
                      })
                    }
                  />
                </div>
                <div>
                  <label className='font-medium' htmlFor='end_time'>{t('field.endTimeLabel')}</label>
                  <input
                    className={fieldClass}
                    type='text'
                    placeholder={t('field.endTime')}
                    value={experience?.endTime}
                    onChange={(e) =>
                      setExperience({ ...experience, endTime: e.target.value })
                    }
                  />
                </div>
              </div>
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.jobPosition')}
                value={experience?.position}
                onChange={(e) =>
                  setExperience({ ...experience, position: e.target.value })
                }
              />
              <textarea
                className={fieldClass}
                rows={3}
                placeholder={t('field.jobDescription')}
                value={experience?.description}
                onChange={(e) =>
                  setExperience({ ...experience, description: e.target.value })
                }
              />
              <ul className='flex flex-col gap-2'>
                {form?.experiences?.map((e, index) => {
                  return (
                    <li className='flex w-full gap-3 rounded-lg bg-surface-2 p-3 text-sm capitalize' key={index}>
                      <p>{index + 1}.</p>
                      <div className='flex w-full flex-col'>
                        <div className='w-full flex justify-between items-center gap-4'>
                          <p className='text-lg font-bold'>{e?.name}</p>
                          <button
                            type='button'
                            className='flex size-7 shrink-0 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-danger-soft hover:text-danger-text'
                            aria-label={t('actions.removeSkill')}
                            onClick={() =>
                              setForm({
                                ...form,
                                experiences: form?.experiences?.filter(
                                  (_, i) => i !== index
                                ),
                              })
                            }
                          >
                            <FaXmark className='size-4' />
                          </button>
                        </div>
                        <p className='text-sm font-medium text-fg-muted'>
                          {e?.startTime} - {e?.endTime}
                        </p>
                        <p className='flex gap-2'>
                          <span>{t('label.position')}</span>
                          <span className='font-bold'>{e?.position}</span>
                        </p>
                        <p className='flex gap-2'>
                          <span>{t('label.description')}</span>
                          <span className='font-medium'>{e?.description}</span>
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ul>
              <button
                className={addButtonClass}
                onClick={handleAddExperience}
              >{t('actions.addExperience')}</button>
            </div>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.education')}</h2>
            <div className='flex flex-col gap-4'>
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.school')}
                value={form?.educationName}
                onChange={(e) =>
                  setForm({ ...form, educationName: e.target.value })
                }
              />
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.major')}
                value={form?.educationMajor}
                onChange={(e) =>
                  setForm({ ...form, educationMajor: e.target.value })
                }
              />
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.completionTime')}
                value={form?.educationCompletion}
                onChange={(e) =>
                  setForm({ ...form, educationCompletion: e.target.value })
                }
              />
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.gpa')}
                value={form?.educationGPA}
                onChange={(e) =>
                  setForm({ ...form, educationGPA: e.target.value })
                }
              />
            </div>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.career')}</h2>
            <p className='text-sm text-fg-muted'>{t('career.hint')}</p>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='flex flex-col gap-2'>
                <label className='font-medium' htmlFor='japaneseLevel'>{t('career.japaneseLevel')}</label>
                <select
                  id='japaneseLevel'
                  className={fieldClass}
                  value={form?.japaneseLevel}
                  onChange={(e) =>
                    setForm({ ...form, japaneseLevel: e.target.value })
                  }
                >
                  <option value=''>{t('level.auto')}</option>
                  {LANGUAGE_LEVELS.map((lv) => (
                    <option key={lv} value={lv}>
                      {t(`level.${lv}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className='flex flex-col gap-2'>
                <label className='font-medium' htmlFor='englishLevel'>{t('career.englishLevel')}</label>
                <select
                  id='englishLevel'
                  className={fieldClass}
                  value={form?.englishLevel}
                  onChange={(e) =>
                    setForm({ ...form, englishLevel: e.target.value })
                  }
                >
                  <option value=''>{t('englishLevel.auto')}</option>
                  {LANGUAGE_LEVELS.map((lv) => (
                    <option key={lv} value={lv}>
                      {t(`englishLevel.${lv}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className='flex flex-col gap-2'>
                <label className='font-medium' htmlFor='yearsOfExperience'>{t('career.years')}</label>
                <input
                  id='yearsOfExperience'
                  className={fieldClass}
                  type='number'
                  min='0'
                  max='50'
                  placeholder={t('career.yearsPlaceholder')}
                  value={form?.yearsOfExperience}
                  onChange={(e) =>
                    setForm({ ...form, yearsOfExperience: e.target.value })
                  }
                />
              </div>
              <div className='flex flex-col gap-2'>
                <label className='font-medium' htmlFor='desiredSalaryMin'>{t('career.salary')}</label>
                <input
                  id='desiredSalaryMin'
                  className={fieldClass}
                  type='number'
                  min='0'
                  step='500000'
                  placeholder={t('career.salaryPlaceholder')}
                  value={form?.desiredSalaryMin}
                  onChange={(e) =>
                    setForm({ ...form, desiredSalaryMin: e.target.value })
                  }
                />
              </div>
              <div className='flex flex-col gap-2 md:col-span-2'>
                <label className='font-medium' htmlFor='desiredLocations'>{t('career.locations')}</label>
                <input
                  id='desiredLocations'
                  className={fieldClass}
                  type='text'
                  placeholder={t('career.locationsPlaceholder')}
                  value={form?.desiredLocations}
                  onChange={(e) =>
                    setForm({ ...form, desiredLocations: e.target.value })
                  }
                />
              </div>
            </div>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.certificates')}</h2>
            <div className='flex flex-col gap-4'>
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.certificateName')}
                value={certificate.name}
                onChange={(e) =>
                  setCertificate({ ...certificate, name: e.target.value })
                }
              />
              <input
                type='file'
                accept='application/pdf'
                onChange={(e) =>
                  setCertificate({
                    ...certificate,
                    certificate: e.target.files[0],
                  })
                }
              />
              <div className='flex flex-col gap-4'>
                {form?.editCertificates?.map((c, index) => {
                  return (
                    <div className='flex flex-col gap-2' key={index}>
                      {c && (
                        <div className='flex flex-col gap-2'>
                          <div>
                            <div className='flex justify-between'>
                              <p>
                                {t('label.certificate')}{' '}
                                <span className='font-bold'>{c?.name}</span>
                              </p>
                              <button
                                type='button'
                                className='flex size-7 shrink-0 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-danger-soft hover:text-danger-text'
                                onClick={() => {
                                  setForm((prevForm) => {
                                    return {
                                      ...prevForm,
                                      editCertificates:
                                        form.editCertificates?.filter(
                                          (e) => e._id !== c._id
                                        ),
                                    };
                                  });
                                }}
                                aria-label={t('actions.removeCertificate')}
                              >
                                <FaXmark className='size-4' />
                              </button>
                            </div>
                            <a
                              href={`${import.meta.env.VITE_BACKEND_URL}/${
                                c?.url
                              }`}
                              download={c.name}
                            >
                              {c.name}
                            </a>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
                {form.certificates?.map((c, index) => {
                  return (
                    <div className='flex flex-col gap-2' key={index}>
                      {c && (
                        <div className='flex flex-col gap-2'>
                          <div>
                            <div className='flex justify-between'>
                              <p>
                                {t('label.certificate')}{' '}
                                <span className='font-bold'>
                                  {form.certificatesName[index]}
                                </span>
                              </p>
                              <button
                                type='button'
                                className='flex size-7 shrink-0 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-danger-soft hover:text-danger-text'
                                onClick={() => {
                                  setForm((prevForm) => {
                                    const newCertificates =
                                      prevForm.certificates?.filter(
                                        (_, i) => i !== index
                                      );
                                    const newCertificatesName =
                                      prevForm.certificatesName?.filter(
                                        (_, i) => i !== index
                                      );

                                    return {
                                      ...prevForm,
                                      certificates: newCertificates,
                                      certificatesName: newCertificatesName,
                                    };
                                  });
                                }}
                                aria-label={t('actions.removeCertificate')}
                              >
                                <FaXmark className='size-4' />
                              </button>
                            </div>
                            <a href={URL.createObjectURL(c)} download={c.name}>
                              {c.name}
                            </a>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
            <button
              className={addButtonClass}
              onClick={handleAddCertificate}
              disabled={isLoadingPost}
            >{t('actions.addCertificate')}</button>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.skills')}</h2>
            <input
              className={fieldClass}
              type='text'
              placeholder={t('field.skill')}
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
            />
            <ul className='flex flex-col gap-2'>
              {form?.skills?.map((s, index) => {
                return (
                  <li
                    className='flex w-full items-center justify-between gap-3 rounded-lg bg-surface-2 p-3 text-sm capitalize'
                    key={index}
                  >
                    <p>
                      <span>{index + 1}.</span>
                      <span>{s}</span>
                    </p>
                    <button
                      type='button'
                      className='flex size-7 shrink-0 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-danger-soft hover:text-danger-text'
                      aria-label={t('actions.removeSkill')}
                      disabled={isLoadingPost}
                      onClick={() =>
                        setForm({
                          ...form,
                          skills: form?.skills?.filter((_, i) => i !== index),
                        })
                      }
                    >
                      <FaXmark className='size-4' />
                    </button>
                  </li>
                );
              })}
            </ul>
            <button
              className={addButtonClass}
              onClick={handleAddSkill}
              disabled={isLoadingPost}
            >{t('actions.addSkill')}</button>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.languages')}</h2>
            <input
              className={fieldClass}
              type='text'
              placeholder={t('field.language')}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            />
            <ul className='flex flex-col gap-2'>
              {form?.languages?.map((l, index) => {
                return (
                  <li
                    className='flex w-full items-center justify-between gap-3 rounded-lg bg-surface-2 p-3 text-sm capitalize'
                    key={index}
                  >
                    <p>
                      <span>{index + 1}.</span>
                      <span>{l}</span>
                    </p>
                    <button
                      type='button'
                      className='flex size-7 shrink-0 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-danger-soft hover:text-danger-text'
                      aria-label={t('actions.removeLanguage')}
                      disabled={isLoadingPost}
                      onClick={() =>
                        setForm({
                          ...form,
                          languages: form?.languages?.filter(
                            (_, i) => i !== index
                          ),
                        })
                      }
                    >
                      <FaXmark className='size-4' />
                    </button>
                  </li>
                );
              })}
            </ul>
            <button
              className={addButtonClass}
              onClick={handleAddLanguage}
              disabled={isLoadingPost}
            >{t('actions.addLanguage')}</button>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-base font-bold text-fg'>{t('section.projects')}</h2>
            <div className='flex flex-col gap-4'>
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.projectName')}
                value={project.name}
                onChange={(e) =>
                  setProject({ ...project, name: e.target.value })
                }
              />
              <input
                className={fieldClass}
                type='text'
                placeholder={t('field.projectTech')}
                value={project.tech}
                onChange={(e) =>
                  setProject({ ...project, tech: e.target.value })
                }
              />
              <textarea
                className={fieldClass}
                placeholder={t('field.projectDescription')}
                rows={3}
                value={project.description}
                onChange={(e) =>
                  setProject({ ...project, description: e.target.value })
                }
              />
            </div>
            <ul className='flex flex-col gap-2'>
              {form?.projects?.map((p, index) => {
                return (
                  <li
                    className='flex w-full flex-col gap-2 rounded-lg bg-surface-2 p-3 text-sm capitalize'
                    key={index}
                  >
                    <div className='flex gap-2'>
                      <p>{index + 1}.</p>
                      <div className='w-full flex flex-col gap-2'>
                        <div className='w-full flex justify-between items-center gap-3'>
                          <p className='flex gap-2'>
                            <span>{t('label.projectName')}</span>
                            <span className='font-bold'>{p?.name}</span>
                          </p>
                          <button
                            type='button'
                            className='flex size-7 shrink-0 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-danger-soft hover:text-danger-text'
                            aria-label={t('actions.removeProject')}
                            disabled={isLoadingPost}
                            onClick={() =>
                              setForm({
                                ...form,
                                projects: form.projects.filter(
                                  (_, i) => i !== index
                                ),
                              })
                            }
                          >
                            <FaXmark className='size-4' />
                          </button>
                        </div>
                        <p className='flex gap-2'>
                          <span>{t('label.tech')}</span>
                          <span className='font-bold'>{p?.tech}</span>
                        </p>
                        <p className='flex gap-2'>
                          <span>{t('label.description')}</span>
                          <span className='font-bold'>{p?.description}</span>
                        </p>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
            <button
              className={addButtonClass}
              onClick={handleAddProject}
              disabled={isLoadingPost}
            >{t('actions.addProject')}</button>
          </div>
          <div className='flex flex-wrap items-center justify-end gap-2 border-t border-line pt-5'>
            <button
              className={previewButtonClass}
              disabled={isLoadingPost}
              onClick={() => setVisibleModal({ visibleResumeModal: form })}
            >{t('actions.downloadPreview')}</button>
            <button
              className={saveButtonClass}
              onClick={handlePostResume}
              disabled={isLoadingPost}
            >{t('actions.save')}</button>
          </div>
        </div>
      </div>
    </Page>
  );
}

export default ResumeLayout;
