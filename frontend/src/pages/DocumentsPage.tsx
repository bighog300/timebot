import axios from 'axios';
import { type ChangeEvent, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { useDocuments, useUploadDocument } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { ProcessingStatusIndicator } from '@/components/documents/ProcessingStatusIndicator';
import { useUIStore } from '@/store/uiStore';

export function DocumentsPage() {
  const { data, isLoading, isError } = useDocuments();
  const { token, loading: authLoading } = useAuth();
  const upload = useUploadDocument();
  const pushToast = useUIStore((s) => s.pushToast);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadDisabledReason = authLoading
    ? 'Authentication is still loading. Please wait a moment.'
    : !token
      ? 'You must be logged in to upload documents.'
      : upload.isPending
        ? 'Upload in progress…'
        : null;

  const onFile = async (file?: File) => {
    if (!file) return;
    try {
      await upload.mutateAsync(file);
      pushToast('Upload queued');
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = typeof error.response?.data?.detail === 'string' ? error.response.data.detail : 'Upload failed';
        console.error('Upload failed:', error.response?.data ?? error.message);
        pushToast(detail);
        return;
      }
      console.error('Upload failed:', error);
      pushToast('Upload failed');
    }
  };

  const onUploadClick = () => {
    if (uploadDisabledReason) {
      pushToast(uploadDisabledReason);
      return;
    }
    inputRef.current?.click();
  };

  const onInputChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    await onFile(selected);
    e.target.value = '';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Documents</h1>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.xlsx,.xls,.ppt,.pptx,.png,.jpg,.jpeg"
          onChange={onInputChange}
        />
        <Button onClick={onUploadClick} disabled={Boolean(uploadDisabledReason)} title={uploadDisabledReason ?? undefined}>
          Upload
        </Button>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message="Failed to load documents" />}
      {data?.length === 0 && <EmptyState label="No documents yet." />}

      <div className="grid gap-3 md:grid-cols-2">
        {data?.map((doc) => (
          <Card key={doc.id}>
            <div className="space-y-2">
              <div className="flex justify-between gap-2">
                <Link className="font-medium text-blue-300 hover:underline" to={`/documents/${doc.id}`}>
                  {doc.filename}
                </Link>
                <ProcessingStatusIndicator status={doc.processing_status} processingError={doc.processing_error} />
              </div>
              {doc.processing_status === 'failed' && doc.processing_error && (
                <div className="rounded border border-red-700 bg-red-950/40 px-3 py-2 text-xs text-red-200">{doc.processing_error}</div>
              )}
              <p className="line-clamp-2 text-sm text-slate-300">{doc.summary ?? 'No summary yet.'}</p>
              <div className="text-xs text-slate-500">{new Date(doc.upload_date).toLocaleString()}</div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
