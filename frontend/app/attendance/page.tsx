'use client';

import { useState, useRef } from 'react';
import { apiClient } from '@/lib/api';
import { AttendanceResult } from '@/lib/types';
import { Upload, Camera, CheckCircle, XCircle, AlertCircle, X } from 'lucide-react';
import Webcam from 'react-webcam';

export default function TakeAttendance() {
  const [photos, setPhotos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [result, setResult] = useState<AttendanceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showWebcam, setShowWebcam] = useState(false);
  const [error, setError] = useState('');
  const webcamRef = useRef<Webcam>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    const newPreviews = files.map((f) => URL.createObjectURL(f));
    setPhotos((prev) => [...prev, ...files]);
    setPreviews((prev) => [...prev, ...newPreviews]);
    setResult(null);
    setError('');
    e.target.value = '';
  };

  const capturePhoto = () => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      fetch(imageSrc)
        .then((res) => res.blob())
        .then((blob) => {
          const file = new File([blob], `attendance-${Date.now()}.jpg`, { type: 'image/jpeg' });
          setPhotos((prev) => [...prev, file]);
          setPreviews((prev) => [...prev, imageSrc]);
          setShowWebcam(false);
          setResult(null);
          setError('');
        });
    }
  };

  const removePhoto = (index: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
    setResult(null);
  };

  const processAttendance = async () => {
    if (photos.length === 0) return;
    setLoading(true);
    setError('');
    try {
      const attendanceResult =
        photos.length === 1
          ? await apiClient.processAttendance(photos[0])
          : await apiClient.processBatchAttendance(photos);
      setResult(attendanceResult);
    } catch (err) {
      setError('Failed to process attendance. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setPhotos([]);
    setPreviews([]);
    setResult(null);
    setError('');
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Process Attendance</h1>
        <p className="text-sm text-gray-600 mt-1">Upload 1–7 classroom photos to automatically mark attendance</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Upload Photos</h2>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800"
            >
              <Upload size={16} />
              <span>Add Photos</span>
            </button>
            <button
              onClick={() => setShowWebcam(!showWebcam)}
              className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50"
            >
              <Camera size={16} />
              <span>{showWebcam ? 'Hide' : 'Capture'}</span>
            </button>
            {photos.length > 0 && (
              <button onClick={clearAll} className="ml-auto text-xs text-gray-500 hover:text-red-600">
                Clear all
              </button>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />

          {showWebcam && (
            <div className="border border-gray-200 p-3">
              <Webcam ref={webcamRef} audio={false} screenshotFormat="image/jpeg" className="w-full mb-3" />
              <div className="flex space-x-2">
                <button onClick={capturePhoto} className="px-4 py-2 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800">
                  Capture
                </button>
                <button onClick={() => setShowWebcam(false)} className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50">
                  Cancel
                </button>
              </div>
            </div>
          )}

          {previews.length === 0 && !showWebcam && (
            <div className="border-2 border-dashed border-gray-200 p-10 text-center text-sm text-gray-400">
              Upload up to 7 classroom photos for better coverage
            </div>
          )}

          {previews.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">
                {photos.length} photo{photos.length !== 1 ? 's' : ''} selected
              </p>
              <div className="grid grid-cols-3 gap-2">
                {previews.map((src, i) => (
                  <div key={i} className="relative group">
                    <img src={src} alt={`Photo ${i + 1}`} className="w-full h-28 object-cover border border-gray-200" />
                    <button
                      onClick={() => removePhoto(i)}
                      className="absolute top-1 right-1 p-1 bg-white border border-gray-300 text-red-600 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {photos.length > 0 && (
            <button
              onClick={processAttendance}
              disabled={loading}
              className="w-full py-2.5 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 disabled:bg-gray-300"
            >
              {loading ? 'Processing...' : `Process ${photos.length > 1 ? `${photos.length} Photos` : 'Attendance'}`}
            </button>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
          )}
        </div>

        <div className="bg-white border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Results</h2>

          {!result ? (
            <div className="text-center text-gray-500 py-16 text-sm">
              Process photos to view attendance results
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-emerald-50 border border-emerald-200 p-4 text-center">
                  <CheckCircle className="text-emerald-600 mx-auto mb-2" size={24} />
                  <p className="text-xl font-semibold text-emerald-900">{result.present.length}</p>
                  <p className="text-xs text-gray-600 uppercase tracking-wide mt-1">Present</p>
                </div>
                <div className="bg-red-50 border border-red-200 p-4 text-center">
                  <XCircle className="text-red-600 mx-auto mb-2" size={24} />
                  <p className="text-xl font-semibold text-red-900">{result.absent.length}</p>
                  <p className="text-xs text-gray-600 uppercase tracking-wide mt-1">Absent</p>
                </div>
                <div className="bg-amber-50 border border-amber-200 p-4 text-center">
                  <AlertCircle className="text-amber-600 mx-auto mb-2" size={24} />
                  <p className="text-xl font-semibold text-amber-900">{result.unrecognized.length}</p>
                  <p className="text-xs text-gray-600 uppercase tracking-wide mt-1">Unknown</p>
                </div>
              </div>

              {result.present.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">Present Students</h3>
                  <div className="space-y-1.5">
                    {result.present.map((student) => (
                      <div key={student.id} className="flex justify-between items-center p-3 bg-emerald-50 border border-emerald-200">
                        <span className="text-sm text-gray-900">{student.name} ({student.roll_no})</span>
                        <span className="text-xs text-gray-500">
                          {student.confidence ? `${(student.confidence * 100).toFixed(1)}%` : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.absent.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">Absent Students</h3>
                  <div className="space-y-1.5">
                    {result.absent.map((student) => (
                      <div key={student.id} className="p-3 bg-red-50 border border-red-200">
                        <span className="text-sm text-gray-900">{student.name} ({student.roll_no})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
