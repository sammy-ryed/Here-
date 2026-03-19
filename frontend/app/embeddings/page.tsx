'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Student, ExtractedFace } from '@/lib/types';
import { Upload, ArrowLeft, CheckCircle, XCircle, Loader2, UserCheck, SkipForward } from 'lucide-react';

type FaceStatus = 'idle' | 'loading' | 'success' | 'error' | 'skipped';

interface FaceState {
  status: FaceStatus;
  message: string;
  assignedName?: string;
}

export default function AddEmbeddings() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (!isAuthenticated || isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // shared
  const [students, setStudents] = useState<Student[]>([]);

  // step 1: upload
  const [step, setStep] = useState<'upload' | 'select'>('upload');
  const [groupPhoto, setGroupPhoto] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [extractLoading, setExtractLoading] = useState(false);
  const [extractError, setExtractError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // step 2: select
  const [faces, setFaces] = useState<ExtractedFace[]>([]);
  const [assignments, setAssignments] = useState<Record<number, number | ''>>({}); // faceIndex â†’ studentId
  const [faceStates, setFaceStates] = useState<Record<number, FaceState>>({});

  useEffect(() => {
    apiClient.getStudents().then(setStudents).catch(console.error);
  }, []);

  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Step 1 handlers
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setGroupPhoto(file);
    setPreviewUrl(URL.createObjectURL(file));
    setExtractError('');
  };

  const handleExtract = async () => {
    if (!groupPhoto) return;
    setExtractLoading(true);
    setExtractError('');
    try {
      const result = await apiClient.extractFaces(groupPhoto);
      if (result.faces.length === 0) {
        setExtractError(result.message || 'No faces detected in this image.');
        return;
      }
      setFaces(result.faces);
      // Initialise assignment + status maps
      const initAssign: Record<number, number | ''> = {};
      const initState: Record<number, FaceState> = {};
      result.faces.forEach((f) => {
        initAssign[f.index] = '';
        initState[f.index] = { status: 'idle', message: '' };
      });
      setAssignments(initAssign);
      setFaceStates(initState);
      setStep('select');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setExtractError(msg || 'Failed to extract faces. Please try again.');
    } finally {
      setExtractLoading(false);
    }
  };

  const handleReset = () => {
    setStep('upload');
    setGroupPhoto(null);
    setPreviewUrl('');
    setFaces([]);
    setAssignments({});
    setFaceStates({});
    setExtractError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Step 2 handlers
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const setFaceStatus = (idx: number, update: Partial<FaceState>) => {
    setFaceStates((prev) => ({ ...prev, [idx]: { ...prev[idx], ...update } }));
  };

  const handleAssign = async (face: ExtractedFace) => {
    const studentId = assignments[face.index];
    if (!studentId) return;
    setFaceStatus(face.index, { status: 'loading', message: '' });
    try {
      const result = await apiClient.assignFace(Number(studentId), face.face_filename);
      setFaceStatus(face.index, {
        status: 'success',
        message: result.message,
        assignedName: result.student_name,
      });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setFaceStatus(face.index, {
        status: 'error',
        message: msg || 'Assignment failed.',
      });
    }
  };

  const handleSkip = (idx: number) => {
    setFaceStatus(idx, { status: 'skipped', message: 'Skipped' });
  };

  const doneCount = Object.values(faceStates).filter((s) => s.status === 'success').length;
  const errorCount = Object.values(faceStates).filter((s) => s.status === 'error').length;
  const skippedCount = Object.values(faceStates).filter((s) => s.status === 'skipped').length;
  const allDone =
    faces.length > 0 &&
    Object.values(faceStates).every((s) => s.status !== 'idle' && s.status !== 'loading');

  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Render
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Add Face Embeddings</h1>
        <p className="text-sm text-gray-600 mt-1">
          Upload a photo, detect all faces, then assign each face to a student.
        </p>
      </div>

      {/* â”€â”€â”€â”€â”€ STEP 1: Upload â”€â”€â”€â”€â”€ */}
      {step === 'upload' && (
        <div className="bg-white border border-gray-200 p-6 max-w-lg">
          <h2 className="text-base font-medium text-gray-900 mb-4">Step 1: Upload a photo</h2>

          <div
            className="border-2 border-dashed border-gray-300 rounded p-8 text-center cursor-pointer hover:border-slate-500 transition-colors mb-4"
            onClick={() => fileInputRef.current?.click()}
          >
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Selected photo"
                className="mx-auto max-h-56 object-contain rounded"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 text-gray-400">
                <Upload size={32} />
                <span className="text-sm">Click to select a photo</span>
              </div>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />

          {extractError && (
            <p className="text-sm text-red-600 mb-3">{extractError}</p>
          )}

          <button
            onClick={handleExtract}
            disabled={!groupPhoto || extractLoading}
            className="w-full py-2.5 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 disabled:bg-gray-300 flex items-center justify-center gap-2"
          >
            {extractLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Detecting faces!
              </>
            ) : (
              <>
                <Upload size={16} />
                Detect Faces
              </>
            )}
          </button>
        </div>
      )}

      {/* â”€â”€â”€â”€â”€ STEP 2: Assign faces â”€â”€â”€â”€â”€ */}
      {step === 'select' && (
        <div>
          {/* Header bar */}
          <div className="flex items-center justify-between mb-5">
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800"
            >
              <ArrowLeft size={16} />
              Upload different photo
            </button>
            <div className="flex gap-4 text-sm text-gray-600">
              <span className="text-emerald-600 font-medium">{doneCount} assigned</span>
              {errorCount > 0 && <span className="text-red-600 font-medium">{errorCount} failed</span>}
              {skippedCount > 0 && <span className="text-gray-400">{skippedCount} skipped</span>}
              <span className="text-gray-400">/ {faces.length} total</span>
            </div>
          </div>

          {allDone && (
            <div className="mb-5 p-3 border border-emerald-200 bg-emerald-50 text-emerald-700 text-sm">
              All faces processed {doneCount} assigned, {skippedCount} skipped
              {errorCount > 0 && `, ${errorCount} failed`}.
              <button onClick={handleReset} className="ml-3 underline font-medium">
                Start over
              </button>
            </div>
          )}

          {/* Face grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {faces.map((face) => {
              const state = faceStates[face.index];
              const isDone = state.status === 'success' || state.status === 'skipped';
              const isLoading = state.status === 'loading';
              const isError = state.status === 'error';

              return (
                <div
                  key={face.index}
                  className={`border rounded overflow-hidden flex flex-col ${
                    state.status === 'success'
                      ? 'border-emerald-300 bg-emerald-50'
                      : state.status === 'skipped'
                      ? 'border-gray-200 bg-gray-50 opacity-50'
                      : isError
                      ? 'border-red-300 bg-red-50'
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  {/* Face thumbnail */}
                  <div className="relative">
                    <img
                      src={face.image_base64}
                      alt={`Face ${face.index + 1}`}
                      className="w-full h-36 object-cover"
                    />
                    {state.status === 'success' && (
                      <div className="absolute top-2 right-2 bg-emerald-500 text-white rounded-full p-0.5">
                        <CheckCircle size={16} />
                      </div>
                    )}
                    {isError && (
                      <div className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-0.5">
                        <XCircle size={16} />
                      </div>
                    )}
                    <span className="absolute bottom-1 left-1 bg-black/50 text-white text-[10px] px-1 rounded">
                      Face {face.index + 1}
                    </span>
                  </div>

                  {/* Controls */}
                  <div className="p-2 flex flex-col gap-2 flex-1">
                    {state.status === 'success' ? (
                      <p className="text-xs text-emerald-700 font-medium flex items-center gap-1">
                        <UserCheck size={12} />
                        {state.assignedName}
                      </p>
                    ) : state.status === 'skipped' ? (
                      <p className="text-xs text-gray-400">Skipped</p>
                    ) : (
                      <>
                        <select
                          value={assignments[face.index] ?? ''}
                          onChange={(e) =>
                            setAssignments((prev) => ({
                              ...prev,
                              [face.index]: e.target.value ? Number(e.target.value) : '',
                            }))
                          }
                          disabled={isDone || isLoading}
                          className="w-full text-xs px-2 py-1.5 border border-gray-300 focus:ring-1 focus:ring-slate-900 focus:border-slate-900 disabled:bg-gray-100"
                        >
                          <option value="">-- student --</option>
                          {students.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} ({s.roll_no})
                            </option>
                          ))}
                        </select>

                        {isError && (
                          <p className="text-[10px] text-red-600">{state.message}</p>
                        )}

                        <div className="flex gap-1.5 mt-auto">
                          <button
                            onClick={() => handleAssign(face)}
                            disabled={!assignments[face.index] || isLoading}
                            className="flex-1 py-1.5 bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 disabled:bg-gray-200 disabled:text-gray-400 flex items-center justify-center gap-1"
                          >
                            {isLoading ? (
                              <Loader2 size={12} className="animate-spin" />
                            ) : (
                              <>
                                <UserCheck size={12} />
                                Assign
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => handleSkip(face.index)}
                            disabled={isLoading}
                            className="px-2 py-1.5 border border-gray-300 text-gray-500 text-xs hover:bg-gray-50 disabled:opacity-50"
                            title="Skip this face"
                          >
                            <SkipForward size={12} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
