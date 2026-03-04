'use client';

import { useState, useRef, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Student } from '@/lib/types';
import { Upload, X, FileImage } from 'lucide-react';

export default function AddEmbeddings() {
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [photos, setPhotos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadStudents();
  }, []);

  const loadStudents = async () => {
    try {
      const data = await apiClient.getStudents();
      setStudents(data);
    } catch (error) {
      console.error('Failed to load students:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setPhotos([...photos, ...files]);
      const newPreviews = files.map((file) => URL.createObjectURL(file));
      setPreviews([...previews, ...newPreviews]);
    }
  };

  const removePhoto = (index: number) => {
    setPhotos(photos.filter((_, i) => i !== index));
    setPreviews(previews.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent || photos.length === 0) {
      setMessage('Please select a student and upload at least one photo');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      await apiClient.addEmbeddings(selectedStudent, photos);
      setMessage('Embeddings added successfully!');
      setPhotos([]);
      setPreviews([]);
      setSelectedStudent(null);
    } catch (error) {
      setMessage('Failed to add embeddings. Please try again.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Add Face Embeddings</h1>
        <p className="text-sm text-gray-600 mt-1">Add additional photos to improve recognition accuracy</p>
      </div>

      <div className="bg-white border border-gray-200 p-6">

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Student
            </label>
            <select
              value={selectedStudent || ''}
              onChange={(e) => setSelectedStudent(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 text-sm focus:ring-1 focus:ring-slate-900 focus:border-slate-900"
              required
            >
              <option value="">-- Choose student --</option>
              {students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.name} ({student.roll_no})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Photos (5–8 per student for best accuracy)
            </label>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800"
            >
              <Upload size={16} />
              <span>Select Photos</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {previews.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Selected Photos ({photos.length})
              </label>
              <div className="grid grid-cols-3 gap-3">
                {previews.map((preview, index) => (
                  <div key={index} className="relative group">
                    <img
                      src={preview}
                      alt={`Preview ${index + 1}`}
                      className="w-full h-32 object-cover border border-gray-200"
                    />
                    <button
                      type="button"
                      onClick={() => removePhoto(index)}
                      className="absolute top-2 right-2 p-1.5 bg-white border border-gray-300 text-red-600 hover:bg-red-50 opacity-0 group-hover:opacity-100"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !selectedStudent || photos.length === 0}
            className="w-full py-2.5 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 disabled:bg-gray-300"
          >
            {loading ? (
              <>Adding Embeddings...</>
            ) : (
              <>Add {photos.length > 0 ? photos.length : ''} Photo{photos.length !== 1 ? 's' : ''}</>
            )}
          </button>

          {message && (
            <div
              className={`p-3 border text-sm ${
                message.includes('success')
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                  : 'bg-red-50 border-red-200 text-red-700'
              }`}
            >
              {message}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
