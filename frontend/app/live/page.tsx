'use client';

import { useState, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { Student } from '@/lib/types';
import { Play, Square, UserCheck } from 'lucide-react';
import Webcam from 'react-webcam';

export default function LiveAttendance() {
  const [isActive, setIsActive] = useState(false);
  const [recognizedStudents, setRecognizedStudents] = useState<Map<number, Student>>(new Map());
  const [currentDetection, setCurrentDetection] = useState<Student | null>(null);
  const [fps, setFps] = useState(0);
  const webcamRef = useRef<Webcam>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const frameCountRef = useRef(0);
  const startTimeRef = useRef(0);

  const processFrame = useCallback(async () => {
    if (!webcamRef.current || !isActive) return;

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) return;

    try {
      frameCountRef.current++;
      
      // Update FPS every 30 frames
      if (frameCountRef.current % 30 === 0) {
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        setFps(Math.round(frameCountRef.current / elapsed));
      }

      // Extract base64 data from data URI (remove "data:image/jpeg;base64," prefix)
      const base64Data = imageSrc.split(',')[1];
      
      const student = await apiClient.recognizeFace(base64Data);
      if (student && student.id) {
        setCurrentDetection(student);
        setRecognizedStudents(prev => {
          const newMap = new Map(prev);
          newMap.set(student.id, student);
          return newMap;
        });
      } else {
        setCurrentDetection(null);
      }
    } catch (error) {
      console.error('Frame processing error:', error);
    }
  }, [isActive]);

  const startCamera = () => {
    setIsActive(true);
    setRecognizedStudents(new Map());
    frameCountRef.current = 0;
    startTimeRef.current = Date.now();
    intervalRef.current = setInterval(processFrame, 1000); // Process every second
  };

  const stopCamera = () => {
    setIsActive(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    setCurrentDetection(null);
  };

  const markPresent = async () => {
    const studentIds = Array.from(recognizedStudents.keys());
    if (studentIds.length === 0) {
      alert('No students recognized yet');
      return;
    }

    // In a real app, you'd have an API endpoint to mark these students present
    alert(`Marking ${studentIds.length} students as present`);
    setRecognizedStudents(new Map());
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Live Attendance</h1>
        <p className="text-sm text-gray-600 mt-1">Real-time face recognition using webcam</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white border border-gray-200 p-6">
          <div className="mb-4 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Camera Feed</h2>
            <div className="text-xs text-gray-500 font-mono">{fps} FPS</div>
          </div>

          <div className="relative bg-black">
            {isActive ? (
              <>
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  className="w-full"
                  videoConstraints={{
                    width: 640,
                    height: 480,
                    facingMode: 'user',
                  }}
                />
                {currentDetection && (
                  <div className="absolute top-4 left-4 bg-emerald-600 text-white px-4 py-2">
                    <p className="font-semibold text-sm">{currentDetection.name}</p>
                    <p className="text-xs opacity-90">{currentDetection.roll_no}</p>
                    {currentDetection.confidence && (
                      <p className="text-xs opacity-75 mt-0.5">
                        {(currentDetection.confidence * 100).toFixed(1)}% match
                      </p>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-96 text-gray-400">
                <div className="text-center">
                  <Play size={48} className="mx-auto mb-3 opacity-40" />
                  <p className="text-sm">Start camera to begin live attendance</p>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 flex space-x-3">
            {!isActive ? (
              <button
                onClick={startCamera}
                className="flex items-center space-x-2 px-5 py-2.5 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800"
              >
                <Play size={16} />
                <span>Start Camera</span>
              </button>
            ) : (
              <button
                onClick={stopCamera}
                className="flex items-center space-x-2 px-5 py-2.5 bg-red-600 text-white text-sm font-medium hover:bg-red-700"
              >
                <Square size={16} />
                <span>Stop Camera</span>
              </button>
            )}
            <button
              onClick={markPresent}
              disabled={recognizedStudents.size === 0}
              className="flex items-center space-x-2 px-5 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
            >
              <UserCheck size={16} />
              <span>Mark Present ({recognizedStudents.size})</span>
            </button>
          </div>
        </div>

        <div className="bg-white border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recognized ({recognizedStudents.size})
          </h2>

          {recognizedStudents.size === 0 ? (
            <div className="text-center text-gray-500 py-12 text-sm">
              <p>No students recognized</p>
              <p className="text-xs mt-2 text-gray-400">Start camera to begin</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {Array.from(recognizedStudents.values()).map((student) => (
                <div
                  key={student.id}
                  className="p-3 bg-emerald-50 border border-emerald-200"
                >
                  <p className="font-medium text-sm text-gray-900">{student.name}</p>
                  <p className="text-xs text-gray-600">{student.roll_no}</p>
                  {student.confidence && (
                    <p className="text-xs text-gray-500 mt-1">
                      {(student.confidence * 100).toFixed(1)}% confidence
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
