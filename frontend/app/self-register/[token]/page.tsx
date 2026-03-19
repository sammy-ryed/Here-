'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { SelfRegisterInfo } from '@/lib/types';
import { Camera, Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import Webcam from 'react-webcam';

type PageState = 'loading' | 'ready' | 'submitting' | 'done' | 'error';

export default function SelfRegisterPage() {
  const params = useParams();
  const token = typeof params.token === 'string' ? params.token : '';

  const [info, setInfo] = useState<SelfRegisterInfo | null>(null);
  const [pageState, setPageState] = useState<PageState>('loading');
  const [errorMsg, setErrorMsg] = useState('');
  const [photos, setPhotos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [showWebcam, setShowWebcam] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [doneInfo, setDoneInfo] = useState<{ name: string; photos_used: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const webcamRef = useRef<Webcam>(null);

  useEffect(() => {
    if (!token) { setPageState('error'); setErrorMsg('Invalid link'); return; }
    apiClient.getSelfRegisterInfo(token)
      .then((data) => {
        setInfo(data);
        setPageState(data.already_registered ? 'done' : 'ready');
        if (data.already_registered) {
          setDoneInfo({ name: data.name, photos_used: 0 });
        }
      })
      .catch((err) => {
        const msg = err?.response?.data?.error || 'This link is invalid or has expired.';
        setErrorMsg(msg);
        setPageState('error');
      });
  }, [token]);

  const addFiles = (files: File[]) => {
    const valid = files.filter(f => f.type.startsWith('image/'));
    const newPreviews = valid.map(f => URL.createObjectURL(f));
    setPhotos(prev => [...prev, ...valid].slice(0, 8));
    setPreviews(prev => [...prev, ...newPreviews].slice(0, 8));
    setSubmitError('');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    addFiles(Array.from(e.target.files || []));
    e.target.value = '';
  };

  const captureFromWebcam = () => {
    const src = webcamRef.current?.getScreenshot();
    if (!src) return;
    fetch(src).then(r => r.blob()).then(blob => {
      const f = new File([blob], `selfie-${Date.now()}.jpg`, { type: 'image/jpeg' });
      addFiles([f]);
      setShowWebcam(false);
    });
  };

  const removePhoto = (i: number) => {
    setPhotos(prev => prev.filter((_, idx) => idx !== i));
    setPreviews(prev => prev.filter((_, idx) => idx !== i));
  };

  const handleSubmit = async () => {
    if (photos.length === 0) { setSubmitError('Please add at least one photo.'); return; }
    setPageState('submitting');
    setSubmitError('');
    try {
      const res = await apiClient.submitSelfRegistration(token, photos) as { name: string; photos_used: number };
      setDoneInfo(res);
      setPageState('done');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
        || 'Registration failed. Please try again.';
      setSubmitError(msg);
      setPageState('ready');
    }
  };

  // ── LOADING ──────────────────────────────────────────────────────────────
  if (pageState === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-3 text-gray-500">
          <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Verifying your link…</span>
        </div>
      </div>
    );
  }

  // ── ERROR / EXPIRED ───────────────────────────────────────────────────────
  if (pageState === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white border border-gray-200 p-8 text-center space-y-4">
          <AlertCircle size={40} className="text-red-500 mx-auto" />
          <h1 className="text-xl font-semibold text-gray-900">Link Unavailable</h1>
          <p className="text-sm text-gray-600">{errorMsg}</p>
          <p className="text-xs text-gray-400">
            If you think this is a mistake, please contact your faculty to request a new registration link.
          </p>
        </div>
      </div>
    );
  }

  // ── DONE ──────────────────────────────────────────────────────────────────
  if (pageState === 'done') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white border border-gray-200 p-8 text-center space-y-4">
          <CheckCircle size={48} className="text-emerald-500 mx-auto" />
          <h1 className="text-xl font-semibold text-gray-900">
            {doneInfo?.photos_used === 0 ? 'Already Registered' : 'Registration Complete!'}
          </h1>
          <p className="text-sm text-gray-700">
            {doneInfo?.photos_used === 0
              ? `${doneInfo?.name}, you have already been registered in the attendance system.`
              : `${doneInfo?.name}, your face has been registered successfully using ${doneInfo?.photos_used} photo${doneInfo?.photos_used !== 1 ? 's' : ''}.`}
          </p>
          <p className="text-xs text-gray-400">
            You can now close this tab. The system will recognise you automatically during attendance.
          </p>
        </div>
      </div>
    );
  }

  // ── SUBMITTING ────────────────────────────────────────────────────────────
  if (pageState === 'submitting') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center space-y-4">
          <div className="w-10 h-10 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-gray-700 font-medium">Processing your photos…</p>
          <p className="text-xs text-gray-400">This may take up to a minute. Please don't close the tab.</p>
        </div>
      </div>
    );
  }

  // ── MAIN FORM ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="max-w-lg w-full space-y-5">

        {/* Header */}
        <div className="bg-white border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-slate-900 flex items-center justify-center shrink-0">
              <span className="text-white font-bold text-sm">FA</span>
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">Face Attendance — Student Registration</h1>
              <p className="text-xs text-gray-500">Your private registration link</p>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 p-4 space-y-1">
            <p className="text-base font-semibold text-gray-900">{info?.name}</p>
            <p className="text-sm text-gray-600 font-mono">Reg. No: {info?.roll_no}</p>
            {info?.email && (
              <p className="text-sm text-gray-600">{info.email}</p>
            )}
            {(info?.course || info?.section) && (
              <p className="text-xs text-gray-500">
                {[info.course, info.section, info.dept, info.room_no].filter(Boolean).join(' · ')}
              </p>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-white border border-gray-200 p-6 space-y-3">
          <h2 className="font-semibold text-gray-900">Take 4–5 photos of yourself</h2>
          <ul className="space-y-1.5 text-sm text-gray-600">
            <li className="flex items-start space-x-2">
              <span className="text-slate-400 mt-0.5">•</span>
              <span>Face the camera directly, in good lighting</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-slate-400 mt-0.5">•</span>
              <span>Try a couple of slight left/right angle shots too</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-slate-400 mt-0.5">•</span>
              <span>Remove glasses or mask for at least some photos</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-slate-400 mt-0.5">•</span>
              <span>Only one face per photo (no group shots)</span>
            </li>
          </ul>
        </div>

        {/* Photo capture */}
        <div className="bg-white border border-gray-200 p-6 space-y-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowWebcam(!showWebcam)}
              className="flex items-center space-x-2 px-4 py-2.5 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800"
            >
              <Camera size={16} />
              <span>{showWebcam ? 'Hide Camera' : 'Take Photo'}</span>
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center space-x-2 px-4 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50"
            >
              <Upload size={16} />
              <span>Upload Photos</span>
            </button>
            {photos.length > 0 && (
              <span className="ml-auto text-xs text-gray-500">{photos.length}/8</span>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file" accept="image/*" multiple
            onChange={handleFileChange}
            className="hidden"
          />

          {showWebcam && (
            <div className="space-y-2">
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                videoConstraints={{ facingMode: 'user' }}
                className="w-full border border-gray-200"
              />
              <div className="flex space-x-2">
                <button onClick={captureFromWebcam} className="px-4 py-2 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800">
                  Capture
                </button>
                <button onClick={() => setShowWebcam(false)} className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50">
                  Cancel
                </button>
              </div>
            </div>
          )}

          {previews.length === 0 && !showWebcam && (
            <div className="border-2 border-dashed border-gray-200 p-8 text-center text-sm text-gray-400">
              No photos added yet
            </div>
          )}

          {previews.length > 0 && (
            <div className="grid grid-cols-4 gap-2">
              {previews.map((src, i) => (
                <div key={i} className="relative group">
                  <img src={src} alt="" className="w-full aspect-square object-cover border border-gray-200" />
                  <button
                    onClick={() => removePhoto(i)}
                    className="absolute top-1 right-1 p-0.5 bg-white border border-gray-300 text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X size={11} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {submitError && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm">{submitError}</div>
        )}

        <button
          onClick={handleSubmit}
          disabled={photos.length === 0}
          className="w-full py-3 bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {photos.length === 0
            ? 'Add photos to continue'
            : `Register with ${photos.length} photo${photos.length !== 1 ? 's' : ''}`}
        </button>

        <p className="text-xs text-center text-gray-400">
          This link is private and single-use. Your photos are stored securely on the college server only.
        </p>
      </div>
    </div>
  );
}
