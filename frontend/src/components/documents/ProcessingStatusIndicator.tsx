type ProcessingStatus = 'uploading' | 'processing' | 'completed' | 'failed' | 'queued';

function normalizeStatus(status: string): ProcessingStatus {
  if (status === 'uploading' || status === 'processing' || status === 'completed' || status === 'failed' || status === 'queued') {
    return status;
  }
  return 'processing';
}

export function ProcessingStatusIndicator({
  status,
  processingError,
  showErrorBanner = false,
  progress,
  message,
}: {
  status: string;
  processingError?: string | null;
  showErrorBanner?: boolean;
  progress?: number;
  message?: string | null;
}) {
  const normalized = normalizeStatus(status);

  return (
    <div className="space-y-2">
      <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-2 py-1 text-xs">
        {(normalized === 'uploading' || normalized === 'processing' || normalized === 'queued') && (
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-500 border-t-blue-400" aria-hidden="true" />
        )}
        {normalized === 'completed' && <span aria-hidden="true">✅</span>}
        {normalized === 'failed' && <span aria-hidden="true">❌</span>}
        <span className="text-slate-300">{normalized}</span>
      </div>
      {typeof progress === 'number' && normalized !== 'completed' && normalized !== 'failed' && (
        <div className="space-y-1">
          <div className="h-2 w-full overflow-hidden rounded bg-slate-800">
            <div className="h-full bg-blue-500" style={{ width: `${Math.max(0, Math.min(100, progress))}%` }} />
          </div>
          {message && <div className="text-xs text-slate-400">{message}</div>}
        </div>
      )}

      {showErrorBanner && normalized === 'failed' && (
        <div className="rounded border border-red-700 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          Processing failed: {processingError ?? 'Unknown processing error.'}
        </div>
      )}
    </div>
  );
}
