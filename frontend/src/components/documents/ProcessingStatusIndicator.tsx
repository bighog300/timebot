type ProcessingStatus = 'uploading' | 'processing' | 'completed' | 'failed';

function normalizeStatus(status: string): ProcessingStatus {
  if (status === 'uploading' || status === 'processing' || status === 'completed' || status === 'failed') {
    return status;
  }
  return 'processing';
}

export function ProcessingStatusIndicator({
  status,
  processingError,
  showErrorBanner = false,
}: {
  status: string;
  processingError?: string | null;
  showErrorBanner?: boolean;
}) {
  const normalized = normalizeStatus(status);

  return (
    <div className="space-y-2">
      <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-2 py-1 text-xs">
        {(normalized === 'uploading' || normalized === 'processing') && (
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-500 border-t-blue-400" aria-hidden="true" />
        )}
        {normalized === 'completed' && <span aria-hidden="true">✅</span>}
        {normalized === 'failed' && <span aria-hidden="true">❌</span>}
        <span className="text-slate-300">{normalized}</span>
      </div>

      {showErrorBanner && normalized === 'failed' && (
        <div className="rounded border border-red-700 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          Processing failed: {processingError ?? 'Unknown processing error.'}
        </div>
      )}
    </div>
  );
}
