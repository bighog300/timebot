import axios from 'axios';
import { type ChangeEvent, type DragEvent, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { useConnections, useDocuments, useGmailImport, useGmailPreview, useUploadDocument } from '@/hooks/useApi';
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
  const { data: connections } = useConnections();
  const gmailPreview = useGmailPreview();
  const gmailImport = useGmailImport();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [senderEmail, setSenderEmail] = useState('');
  const [maxResults, setMaxResults] = useState(20);
  const [includeAttachments, setIncludeAttachments] = useState(false);
  const [previewMessages, setPreviewMessages] = useState<Array<{ gmail_message_id: string; sender: string; subject: string; received_at: string | null; snippet: string; already_imported: boolean }>>([]);
  const [selectedMessageIds, setSelectedMessageIds] = useState<string[]>([]);
  const [gmailError, setGmailError] = useState<string | null>(null);

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



  const acceptedExtensions = new Set(['pdf','doc','docx','txt','xlsx','xls','ppt','pptx','png','jpg','jpeg']);

  const onFiles = async (files: FileList | File[]) => {
    const items = Array.from(files);
    for (const file of items) {
      const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
      if (!acceptedExtensions.has(ext)) {
        pushToast(`Unsupported file type: .${ext || 'unknown'}`);
        continue;
      }
      await onFile(file);
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
    if (e.target.files) await onFiles(e.target.files);
    e.target.value = '';
  };

  const onDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (uploadDisabledReason) {
      pushToast(uploadDisabledReason);
      return;
    }
    if (e.dataTransfer.files?.length) await onFiles(e.dataTransfer.files);
  };

  const gmailConnection = useMemo(() => connections?.find((connection) => connection.type === 'gmail'), [connections]);
  const oauthReady = Boolean(gmailConnection?.is_authenticated);
  const gmailConfigured = gmailConnection?.provider_is_configured ?? oauthReady;
  const previewDisabled = gmailPreview.isPending || !senderEmail.trim() || !oauthReady || !gmailConfigured;

  const onGmailPreview = async () => {
    setPreviewMessages([]);
    setSelectedMessageIds([]);
    setGmailError(null);
    try {
      const response = await gmailPreview.mutateAsync({
        sender_email: senderEmail.trim(),
        max_results: maxResults,
        include_attachments: includeAttachments,
      });
      setPreviewMessages(response.messages);
    } catch (error) {
      const detail = typeof (axios.isAxiosError(error) ? error.response?.data?.detail : null) === 'string'
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? ''
        : '';
      if (detail.toLowerCase().includes('oauth') || detail.toLowerCase().includes('configured')) {
        setGmailError('Gmail is not connected or not configured.');
        return;
      }
      setGmailError(detail || 'Gmail is not connected or not configured.');
    }
  };

  const onGmailImport = async () => {
    try {
      const result = await gmailImport.mutateAsync({
        sender_email: senderEmail.trim(),
        message_ids: selectedMessageIds,
        include_attachments: includeAttachments,
      });
      pushToast(`Imported ${result.imported_email_count} emails and ${result.imported_attachment_count} attachments. Skipped ${result.skipped_attachment_count} unsupported attachments.`);
      if (result.skipped_attachments?.length) {
        pushToast(`Skipped attachments: ${result.skipped_attachments.map((a: { filename: string; reason: string }) => `${a.filename} (${a.reason})`).join(', ')}`);
      }
      setPreviewMessages((current) =>
        current.map((message) => (selectedMessageIds.includes(message.gmail_message_id) ? { ...message, already_imported: true } : message)),
      );
      setSelectedMessageIds([]);
    } catch {
      pushToast('Gmail import failed');
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Documents</h1>
      <div
        className={`rounded-lg border-2 p-4 transition-colors sm:p-6 ${isDragging ? 'border-blue-400 bg-blue-950/30' : 'border-dashed border-slate-600 bg-slate-900/40'}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        role="region"
        aria-label="Document upload drop zone"
        data-testid="documents-dropzone"
      >
        <div className="flex flex-col items-start gap-3">
          <div>
            <p className="text-base font-semibold">Drag and drop documents here</p>
            <p className="text-sm text-slate-300">PDF, Word, Excel, PowerPoint, text, and image files supported</p>
          </div>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          multiple
          accept=".pdf,.doc,.docx,.txt,.xlsx,.xls,.ppt,.pptx,.png,.jpg,.jpeg"
          onChange={onInputChange}
        />
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-300">
            <Button onClick={onUploadClick} disabled={Boolean(uploadDisabledReason)} title={uploadDisabledReason ?? undefined}>
              {upload.isPending ? 'Uploading…' : 'Choose files'}
            </Button>
            <span>or choose files</span>
          </div>
        </div>
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

      <Card>
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Import from Gmail</h2>
          <div className="grid gap-2 md:grid-cols-4">
            <input className="rounded border border-slate-700 bg-slate-900 p-2 text-sm" placeholder="sender@example.com" value={senderEmail} onChange={(e) => setSenderEmail(e.target.value)} />
            <input className="rounded border border-slate-700 bg-slate-900 p-2 text-sm" type="number" min={1} max={100} value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value) || 20)} />
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={includeAttachments} onChange={(e) => setIncludeAttachments(e.target.checked)} />Include attachments</label>
            <Button onClick={onGmailPreview} disabled={previewDisabled}>{gmailPreview.isPending ? 'Previewing…' : 'Preview'}</Button>
          </div>
          {!oauthReady && <div className="text-sm text-yellow-300">Gmail is not connected or not configured.</div>}
          {gmailError && <div className="text-sm text-red-300">{gmailError}</div>}
          {previewMessages.length === 0 && !gmailPreview.isPending && senderEmail.trim() && !gmailError && <EmptyState label="No messages found for this sender" />}
          {previewMessages.length > 0 && (
            <div className="space-y-2">
              {previewMessages.map((message) => (
                <div key={message.gmail_message_id} className="rounded border border-slate-700 p-2">
                  <div className="flex items-start justify-between gap-2">
                    <label className="flex items-start gap-2">
                      <input
                        type="checkbox"
                        checked={selectedMessageIds.includes(message.gmail_message_id)}
                        disabled={message.already_imported}
                        onChange={(e) => setSelectedMessageIds((curr) => e.target.checked ? [...curr, message.gmail_message_id] : curr.filter((id) => id !== message.gmail_message_id))}
                      />
                      <div>
                        <div className="font-medium">{message.subject}</div>
                        <div className="text-xs text-slate-400">{message.sender} • {message.received_at ? new Date(message.received_at).toLocaleString() : 'Unknown date'}</div>
                        <div className="text-sm text-slate-300">{message.snippet}</div>
                      </div>
                    </label>
                    {message.already_imported && <span className="rounded bg-slate-700 px-2 py-1 text-xs">already imported</span>}
                  </div>
                </div>
              ))}
              <Button onClick={onGmailImport} disabled={gmailImport.isPending || selectedMessageIds.length === 0}>
                {gmailImport.isPending ? 'Importing…' : 'Import selected'}
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
