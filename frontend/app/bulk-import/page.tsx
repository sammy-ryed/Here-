'use client';

import { useState, useRef, useCallback } from 'react';
import * as XLSX from 'xlsx';
import { apiClient } from '@/lib/api';
import { BulkImportResult, BulkImportTokenEntry, BulkImportStudentResult } from '@/lib/types';
import { Upload, FileSpreadsheet, CheckCircle, XCircle, AlertCircle, Copy, Download, ChevronDown, ChevronUp, Clock } from 'lucide-react';

export default function BulkImport() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<BulkImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showInstructions, setShowInstructions] = useState(true);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selfRegBaseUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/self-register`
    : '/self-register';

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) { setFile(f); setResult(null); setError(''); }
    e.target.value = '';
  };

  const handleImport = async () => {
    if (!file) return;
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await apiClient.bulkImportStudents(file);
      setResult(res);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
        || 'Import failed. Check backend logs for details.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const copyLink = useCallback((token: string) => {
    navigator.clipboard.writeText(`${selfRegBaseUrl}/${token}`);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2000);
  }, [selfRegBaseUrl]);

  const downloadLinksCSV = () => {
    if (!result?.tokens) return;
    const header = 'Name,Roll No,Registration Link,Status';
    const rows = result.tokens.map(t =>
      `"${t.name}","${t.roll_no}","${t.token ? `${selfRegBaseUrl}/${t.token}` : ''}","${t.status}"`
    );
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'registration_links.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const downloadTemplate = () => {
    const headers = ['Name', 'Roll No', 'Section', 'Course', 'Department', 'Room No'];
    const ws = XLSX.utils.aoa_to_sheet([headers]);
    // Column widths
    ws['!cols'] = [22, 14, 10, 18, 22, 10].map(w => ({ wch: w }));
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Students');
    XLSX.writeFile(wb, 'students_template.xlsx');
  };

  const driveStatusRow = (s: BulkImportStudentResult) => {
    if (s.status === 'success') return 'bg-emerald-50 border-l-2 border-emerald-400';
    if (s.status === 'failed')  return 'bg-red-50 border-l-2 border-red-400';
    return 'bg-amber-50 border-l-2 border-amber-400';
  };
  const driveStatusIcon = (s: BulkImportStudentResult['status']) => {
    if (s === 'success') return <CheckCircle size={15} className="text-emerald-600" />;
    if (s === 'failed')  return <XCircle size={15} className="text-red-600" />;
    return <AlertCircle size={15} className="text-amber-500" />;
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Bulk Import Students</h1>
        <p className="text-sm text-gray-600 mt-1">
          Upload an Excel sheet to add all students at once — no photos needed from faculty
        </p>
      </div>

      {/* Instructions */}
      <div className="bg-white border border-gray-200">
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="w-full flex items-center justify-between px-5 py-4 text-left"
        >
          <span className="text-sm font-semibold text-gray-900 flex items-center space-x-2">
            <FileSpreadsheet size={16} className="text-slate-600" />
            <span>How the Excel sheet should look</span>
          </span>
          {showInstructions ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
        </button>

        {showInstructions && (
          <div className="px-5 pb-5 border-t border-gray-100 space-y-5">

            {/* Mode A — tokens */}
            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wide bg-slate-900 text-white px-2 py-0.5">Mode A</span>
                <p className="text-sm font-semibold text-slate-900">Self-Registration (recommended)</p>
              </div>
              <p className="text-sm text-gray-600">
                Upload an Excel with student details — <strong>no photos needed from you</strong>.
                The system creates a private one-time link per student. Send the links out; each student opens
                their link and submits their own photos. Links expire in <strong>7 days</strong>.
              </p>
              <p className="text-sm text-gray-600">
                This mode is auto-selected whenever the sheet has <strong>no "Drive Link" column</strong>.
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border border-gray-200">
                  <thead>
                    <tr className="bg-gray-50">
                      {['Column header', 'Required?', 'Example'].map(h => (
                        <th key={h} className="text-left px-4 py-2 font-semibold text-gray-700 border-b border-gray-200 text-xs">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-xs">
                    {[
                      ['Name',       true,  'Rahul Sharma'],
                      ['Roll No',    true,  'CS2024001'],
                      ['Section',    false, 'A'],
                      ['Course',     false, 'B.Tech CSE'],
                      ['Department', false, 'Computer Science'],
                      ['Room No',    false, '301'],
                    ].map(([col, req, ex]) => (
                      <tr key={String(col)}>
                        <td className="px-4 py-2 font-mono text-gray-800">{String(col)}</td>
                        <td className="px-4 py-2">
                          <span className={`px-2 py-0.5 ${req ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'}`}>
                            {req ? 'Required' : 'Optional'}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-gray-500">{String(ex)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-3 pt-1">
                <button
                  onClick={downloadTemplate}
                  className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 text-sm text-slate-700 hover:bg-slate-50 font-medium"
                >
                  <Download size={14} />
                  Download Excel Template
                </button>
                <span className="text-xs text-gray-400">After import, copy or download all student links from the results table below.</span>
              </div>
            </div>

            {/* Mode B — drive */}
            <div className="border-t border-gray-100 pt-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wide bg-gray-500 text-white px-2 py-0.5">Mode B</span>
                <p className="text-sm font-semibold text-gray-700">Drive Links (instant registration)</p>
              </div>
              <p className="text-sm text-gray-600">
                Add a <code className="bg-gray-100 px-1 text-xs font-mono">Drive Link</code> column containing a public Google Drive <em>folder</em> link
                for each student. The system downloads up to 8 photos per student, detects the face, and registers
                them immediately — no token links are generated.
              </p>
              <p className="text-xs text-gray-500">
                The Drive folder must be shared as <strong>"Anyone with the link can view"</strong>. Only .jpg / .jpeg / .png / .webp / .bmp files are used.
              </p>
            </div>

          </div>
        )}
      </div>

      {/* Upload */}
      <div className="bg-white border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Upload Excel File</h2>

        <div className="flex items-center space-x-4">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50"
          >
            <Upload size={16} />
            <span>{file ? 'Change file' : 'Choose .xlsx file'}</span>
          </button>
          {file && (
            <span className="text-sm text-gray-700">
              <span className="font-medium">{file.name}</span>
              <span className="text-gray-400 ml-2">({(file.size / 1024).toFixed(1)} KB)</span>
            </span>
          )}
        </div>

        <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileSelect} className="hidden" />

        {file && !loading && (
          <button onClick={handleImport} className="px-6 py-2.5 bg-slate-900 text-white text-sm font-medium hover:bg-slate-800">
            Start Import
          </button>
        )}

        {loading && (
          <div className="space-y-1.5">
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-gray-600">Importing students…</span>
            </div>
            <p className="text-xs text-gray-400">Please wait and do not close this tab.</p>
          </div>
        )}

        {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>}
      </div>

      {/* Token mode results */}
      {(result?.mode === 'tokens' || result?.mode === 'mixed') && result.tokens && result.tokens.length > 0 && (
        <div className="bg-white border border-gray-200 p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Registration Links Generated</h2>
            <button
              onClick={downloadLinksCSV}
              className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50"
            >
              <Download size={15} />
              <span>Download CSV</span>
            </button>
          </div>

          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Links Generated', value: result.pending ?? 0, cls: 'bg-blue-50 border-blue-200 text-blue-900' },
              { label: 'Skipped',         value: result.skipped,      cls: 'bg-amber-50 border-amber-200 text-amber-900' },
              { label: 'Failed',          value: result.failed,       cls: 'bg-red-50 border-red-200 text-red-900' },
            ].map(({ label, value, cls }) => (
              <div key={label} className={`border p-4 text-center ${cls}`}>
                <p className="text-2xl font-semibold">{value}</p>
                <p className="text-xs uppercase tracking-wide text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>

          <div className="bg-blue-50 border border-blue-200 p-3 text-sm text-blue-800 flex items-start space-x-2">
            <Clock size={15} className="mt-0.5 shrink-0" />
            <span>Links expire in <strong>7 days</strong>. Each link is single-use — valid only for that student. Share via WhatsApp, email, or your college LMS. Download the CSV to get all links at once.</span>
          </div>

          {/* Links table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-y border-gray-200">
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Name</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Roll No</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Registration Link</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {result.tokens.map((t: BulkImportTokenEntry, i: number) => (
                  <tr key={i} className={t.status === 'pending' ? '' : 'bg-amber-50'}>
                    <td className="px-4 py-2.5 font-medium text-gray-900">{t.name}</td>
                    <td className="px-4 py-2.5 text-gray-600 font-mono text-xs">{t.roll_no}</td>
                    <td className="px-4 py-2.5">
                      {t.token ? (
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs text-gray-500 truncate max-w-xs">
                            {selfRegBaseUrl}/{t.token.slice(0, 16)}…
                          </span>
                          <button
                            onClick={() => copyLink(t.token!)}
                            className="flex items-center space-x-1 px-2 py-1 border border-gray-300 text-xs text-gray-600 hover:bg-gray-50 shrink-0"
                          >
                            <Copy size={12} />
                            <span>{copiedToken === t.token ? 'Copied!' : 'Copy'}</span>
                          </button>
                        </div>
                      ) : (
                        <span className="text-gray-400 text-xs">{t.message}</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`text-xs px-2 py-0.5 ${
                        t.status === 'pending' ? 'bg-blue-100 text-blue-700' :
                        t.status === 'skipped' ? 'bg-amber-100 text-amber-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {t.status === 'pending' ? 'Link sent' : t.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Drive mode results */}
      {(result?.mode === 'drive' || result?.mode === 'mixed') && result.results && result.results.length > 0 && (
        <div className="bg-white border border-gray-200 p-6 space-y-5">
          <h2 className="text-lg font-semibold text-gray-900">Import Results</h2>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Total',      value: result.total,          cls: 'bg-gray-50 border-gray-200 text-gray-900' },
              { label: 'Registered', value: result.registered ?? 0, cls: 'bg-emerald-50 border-emerald-200 text-emerald-900' },
              { label: 'Failed',     value: result.failed,          cls: 'bg-red-50 border-red-200 text-red-900' },
              { label: 'Skipped',    value: result.skipped,         cls: 'bg-amber-50 border-amber-200 text-amber-900' },
            ].map(({ label, value, cls }) => (
              <div key={label} className={`border p-4 text-center ${cls}`}>
                <p className="text-2xl font-semibold">{value}</p>
                <p className="text-xs uppercase tracking-wide text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-y border-gray-200">
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Name</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Roll No</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Status</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-700">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {result.results.map((r: BulkImportStudentResult, i: number) => (
                  <tr key={i} className={driveStatusRow(r)}>
                    <td className="px-4 py-2.5 font-medium text-gray-900">{r.name || '—'}</td>
                    <td className="px-4 py-2.5 text-gray-700 font-mono text-xs">{r.roll_no}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center space-x-1.5">
                        {driveStatusIcon(r.status)}
                        <span className="capitalize text-xs font-medium">{r.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-gray-600 text-xs">{r.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
