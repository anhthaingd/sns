import React, { useCallback, useContext, useEffect, useState } from 'react';
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
import {
  useGetResumeQuery,
  usePostResumeMutation,
} from '../../../services/redux/query/usersQuery';
import { ModalContext } from '../../../context/ModalProvider';
function ResumeLayout() {
  const { state, setVisibleModal } = useContext(ModalContext);
  const { data: resumeData, isSuccess: isSuccessResume } = useGetResumeQuery();
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
    setForm({ ...form, experiences: [...form?.experiences, experience] });
    setExperience(() => {
      return { name: '', startTime: '', endTime: '' };
    });
  }, [experience, form]);
  const handleAddCertificate = useCallback(() => {
    if (!certificate.name || !certificate.certificate) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: 'Chứng chỉ yêu cầu có tên và file dạng pdf!',
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
  }, [certificate, form, setVisibleModal]);
  const handleAddSkill = useCallback(() => {
    setForm({ ...form, skills: [...form?.skills, skill] });
    setSkill(() => {
      return '';
    });
  }, [skill, form]);
  const handleAddLanguage = useCallback(() => {
    setForm({ ...form, languages: [...form?.languages, language] });
    setLanguage(() => {
      return '';
    });
  }, [language, form]);
  const handleAddProject = useCallback(() => {
    setForm({ ...form, projects: [...form?.projects, project] });
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
  useEffect(() => {
    if (isSuccessPost && postData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: postData?.message,
        },
      });
    }
    if (isErrorPost && errorPost) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorPost?.data?.message,
        },
      });
    }
  }, [isSuccessPost, postData, isErrorPost, errorPost, setVisibleModal]);
  return (
    <Page>
      {state.visibleResumeModal && <ResumeModal />}
      <div className='flex flex-col gap-8' aria-disabled={isLoadingPost}>
        <h1 className='text-center text-2xl font-bold'>Create your resume</h1>
        <div className='bg-neutral-50 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 px-4 py-8 flex flex-col gap-6 rounded'>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Basic info</h2>
            <div>
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='file'
                accept='image/*,.jpeg,.jpg,.png,.webp'
                placeholder='Upload your avatar name...'
                onChange={(e) =>
                  setForm({ ...form, avatar: e.target.files?.[0] })
                }
              />
              <p className='italic text-sm'>
                (Only *.jpeg, *.webp and *.png images will be accepted)
              </p>
              {form.avatar && (
                <img
                  className='w-[170px] h-[180px] object-cover'
                  src={URL.createObjectURL(form.avatar)}
                  alt={form.avatar?.filename}
                  {...{ fetchPriority: 'low' }}
                />
              )}
              {form.oldAvatar && !form.avatar && (
                <img
                  className='w-[170px] h-[180px] object-cover'
                  src={`${import.meta.env.VITE_BACKEND_URL}/${
                    form.oldAvatar?.url
                  }`}
                  alt={form.oldAvatar?.name}
                  {...{ fetchPriority: 'low' }}
                />
              )}
            </div>
            <input
              className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
              type='text'
              placeholder='Enter your full name...'
              value={form?.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
              type='text'
              placeholder='Enter your position that you apply for...'
              value={form?.position}
              onChange={(e) => setForm({ ...form, position: e.target.value })}
            />
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Contact</h2>
            <div className='flex flex-col gap-4'>
              <div className='flex items-center gap-4'>
                <label
                  className='p-2 rounded-full bg-neutral-700 flex justify-center items-center'
                  htmlFor='date'
                >
                  <FaCakeCandles className='text-neutral-100' />
                </label>
                <input
                  className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
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
                  className='p-2 rounded-full bg-neutral-700 flex justify-center items-center'
                  htmlFor='email'
                >
                  <FaEnvelope className='text-neutral-100' />
                </label>
                <input
                  className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                  type='email'
                  placeholder='Enter your email...'
                  required
                  value={form?.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div className='flex items-center gap-4'>
                <label
                  className='p-2 rounded-full bg-neutral-700 flex justify-center items-center'
                  htmlFor='address'
                >
                  <FaLocationDot className='text-neutral-100' />
                </label>
                <input
                  className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                  type='text'
                  placeholder='Enter your address...'
                  value={form?.address}
                  onChange={(e) =>
                    setForm({ ...form, address: e.target.value })
                  }
                />
              </div>
              <div className='flex items-center gap-4'>
                <label
                  className='p-2 rounded-full bg-neutral-700 flex justify-center items-center'
                  htmlFor='phone'
                >
                  <FaPhone className='text-neutral-100' />
                </label>
                <input
                  className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                  type='number'
                  placeholder='Enter your phone number...'
                  value={form?.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </div>
              <div className='flex items-center gap-4'>
                <label
                  className='p-2 rounded-full bg-neutral-700 flex justify-center items-center'
                  htmlFor='github'
                >
                  <FaGithub className='text-neutral-100' />
                </label>
                <input
                  className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                  placeholder='https://yourgithub.com'
                  pattern='https://.*'
                  value={form?.github}
                  onChange={(e) => setForm({ ...form, github: e.target.value })}
                />
              </div>
            </div>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Objective</h2>
            <textarea
              className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded focus:outline-none'
              placeholder='Enter your objective...'
              rows={3}
              value={form?.objective}
              onChange={(e) => setForm({ ...form, objective: e.target.value })}
            />
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Experience</h2>
            <div className='flex flex-col gap-4'>
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter name company...'
                value={experience?.name}
                onChange={(e) =>
                  setExperience({ ...experience, name: e.target.value })
                }
              />
              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <label className='font-medium' htmlFor='start_time'>
                    Start Time
                  </label>
                  <input
                    className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                    type='text'
                    placeholder='Enter start time...'
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
                  <label className='font-medium' htmlFor='end_time'>
                    End Time
                  </label>
                  <input
                    className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                    type='text'
                    placeholder='Enter end time...'
                    value={experience?.endTime}
                    onChange={(e) =>
                      setExperience({ ...experience, endTime: e.target.value })
                    }
                  />
                </div>
              </div>
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter your position...'
                value={experience?.position}
                onChange={(e) =>
                  setExperience({ ...experience, position: e.target.value })
                }
              />
              <textarea
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded focus:outline-none'
                rows={3}
                placeholder='Enter your description...'
                value={experience?.description}
                onChange={(e) =>
                  setExperience({ ...experience, description: e.target.value })
                }
              />
              <ul className='flex flex-col gap-2 list-decimal'>
                {form?.experiences?.map((e, index) => {
                  return (
                    <li className='w-full capitalize flex gap-2' key={index}>
                      <p>{index + 1}.</p>
                      <div className='w-f ull flex flex-col'>
                        <div className='w-full flex justify-between items-center gap-4'>
                          <p className='text-lg font-bold'>{e?.name}</p>
                          <button
                            aria-label='delete-skill'
                            onClick={() =>
                              setForm({
                                ...form,
                                experiences: form?.experiences?.filter(
                                  (_, i) => i !== index
                                ),
                              })
                            }
                          >
                            <FaXmark />
                          </button>
                        </div>
                        <p className='text-sm font-medium italic'>
                          {e?.startTime} - {e?.endTime}
                        </p>
                        <p className='flex gap-2'>
                          <span>Position:</span>
                          <span className='font-bold'>{e?.position}</span>
                        </p>
                        <p className='flex gap-2'>
                          <span>Description</span>
                          <span className='font-medium'>{e?.description}</span>
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ul>
              <button
                className='bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-700 text-white px-4 py-2 rounded font-bold'
                onClick={handleAddExperience}
              >
                Add Experience
              </button>
            </div>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Education</h2>
            <div className='flex flex-col gap-4'>
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter your College/School...'
                value={form?.educationName}
                onChange={(e) =>
                  setForm({ ...form, educationName: e.target.value })
                }
              />
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter your major...'
                value={form?.educationMajor}
                onChange={(e) =>
                  setForm({ ...form, educationMajor: e.target.value })
                }
              />
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter your completion time...'
                value={form?.educationCompletion}
                onChange={(e) =>
                  setForm({ ...form, educationCompletion: e.target.value })
                }
              />
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter your GPA...'
                value={form?.educationGPA}
                onChange={(e) =>
                  setForm({ ...form, educationGPA: e.target.value })
                }
              />
            </div>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Certificates</h2>
            <div className='flex flex-col gap-4'>
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter certificate name...'
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
                                Certificate:{' '}
                                <span className='font-bold'>{c?.name}</span>
                              </p>
                              <button
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
                                aria-label='delete-certificate'
                              >
                                <FaXmark className='text-lg' />
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
                                Certificate:{' '}
                                <span className='font-bold'>
                                  {form.certificatesName[index]}
                                </span>
                              </p>
                              <button
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
                                aria-label='delete-certificate'
                              >
                                <FaXmark className='text-lg' />
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
              className='bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-700 text-white px-4 py-2 rounded font-bold'
              onClick={handleAddCertificate}
              disabled={isLoadingPost}
            >
              Add Certificate
            </button>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Skills</h2>
            <input
              className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
              type='text'
              placeholder='Enter your skill...'
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
            />
            <ul className='flex flex-col gap-2 list-decimal'>
              {form?.skills?.map((s, index) => {
                return (
                  <li
                    className='w-full capitalize flex justify-between items-center list-decimal'
                    key={index}
                  >
                    <p>
                      <span>{index + 1}.</span>
                      <span>{s}</span>
                    </p>
                    <button
                      aria-label='delete-skill'
                      disabled={isLoadingPost}
                      onClick={() =>
                        setForm({
                          ...form,
                          skills: form?.skills?.filter((_, i) => i !== index),
                        })
                      }
                    >
                      <FaXmark />
                    </button>
                  </li>
                );
              })}
            </ul>
            <button
              className='bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-700 text-white px-4 py-2 rounded font-bold'
              onClick={handleAddSkill}
              disabled={isLoadingPost}
            >
              Add Skill
            </button>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Languages</h2>
            <input
              className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
              type='text'
              placeholder='Enter your language...'
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            />
            <ul className='flex flex-col gap-2 list-decimal'>
              {form?.languages?.map((l, index) => {
                return (
                  <li
                    className='w-full capitalize flex justify-between items-center list-decimal'
                    key={index}
                  >
                    <p>
                      <span>{index + 1}.</span>
                      <span>{l}</span>
                    </p>
                    <button
                      aria-label='delete-language'
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
                      <FaXmark />
                    </button>
                  </li>
                );
              })}
            </ul>
            <button
              className='bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-700 text-white px-4 py-2 rounded font-bold'
              onClick={handleAddLanguage}
              disabled={isLoadingPost}
            >
              Add Language
            </button>
          </div>
          <div className='flex flex-col gap-4'>
            <h2 className='text-xl font-bold'>Projects</h2>
            <div className='flex flex-col gap-4'>
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter project name...'
                value={project.name}
                onChange={(e) =>
                  setProject({ ...project, name: e.target.value })
                }
              />
              <input
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded'
                type='text'
                placeholder='Enter tech stack...'
                value={project.tech}
                onChange={(e) =>
                  setProject({ ...project, tech: e.target.value })
                }
              />
              <textarea
                className='dark:bg-neutral-700 w-full px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded focus:outline-none'
                placeholder='Enter description...'
                rows={3}
                value={project.description}
                onChange={(e) =>
                  setProject({ ...project, description: e.target.value })
                }
              />
            </div>
            <ul className='flex flex-col gap-2 list-decimal'>
              {form?.projects?.map((p, index) => {
                return (
                  <li
                    className='w-full capitalize flex flex-col gap-2'
                    key={index}
                  >
                    <div className='flex gap-2'>
                      <p>{index + 1}.</p>
                      <div className='w-full flex flex-col gap-2'>
                        <div className='w-full flex justify-between items-center gap-3'>
                          <p className='flex gap-2'>
                            <span>Project name:</span>
                            <span className='font-bold'>{p?.name}</span>
                          </p>
                          <button
                            aria-label='delete-project'
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
                            <FaXmark />
                          </button>
                        </div>
                        <p className='flex gap-2'>
                          <span>Tech:</span>
                          <span className='font-bold'>{p?.tech}</span>
                        </p>
                        <p className='flex gap-2'>
                          <span>Description</span>
                          <span className='font-bold'>{p?.description}</span>
                        </p>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
            <button
              className='bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-700 text-white px-4 py-2 rounded font-bold'
              onClick={handleAddProject}
              disabled={isLoadingPost}
            >
              Add Project
            </button>
          </div>
          <div className='flex justify-center items-center gap-4'>
            <button
              className='bg-neutral-700 text-white px-4 py-2 font-bold hover:bg-neutral-800 dark:bg-neutral-200 dark:hover:bg-neutral-50 dark:text-neutral-700 transition-colors'
              onClick={handlePostResume}
              disabled={isLoadingPost}
            >
              Save
            </button>
            <button
              className='px-4 py-2 bg-blue-500 hover:bg-blue-700 transition-colors text-white font-bold'
              disabled={isLoadingPost}
              onClick={() => setVisibleModal({ visibleResumeModal: form })}
            >
              DOWNLOAD/PREVIEW
            </button>
          </div>
        </div>
      </div>
    </Page>
  );
}

export default ResumeLayout;
