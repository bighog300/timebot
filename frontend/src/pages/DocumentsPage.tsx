import { Link } from 'react-router-dom';
import { useDocuments, useUploadDocument } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { useUIStore } from '@/store/uiStore';

export function DocumentsPage() {
  const { data, isLoading, isError } = useDocuments();
  const upload = useUploadDocument();
  const pushToast = useUIStore((s) => s.pushToast);

  const onFile = async (file?: File) => {
    if (!file) return;
    try {
      await upload.mutateAsync(file);
      pushToast('Upload queued');
    } catch {
      pushToast('Upload failed');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Documents</h1>
        <label className="cursor-pointer">
          <input type="file" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} />
          <Button>Upload</Button>
        </label>
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
                <span className="text-xs text-slate-400">{doc.processing_status}</span>
              </div>
              <p className="line-clamp-2 text-sm text-slate-300">{doc.summary ?? 'No summary yet.'}</p>
              <div className="text-xs text-slate-500">{new Date(doc.upload_date).toLocaleString()}</div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
