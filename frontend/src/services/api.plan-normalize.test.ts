import { describe, expect, it } from 'vitest';
import { normalizeAdminPlanPatchPayload } from './api';

describe('normalizeAdminPlanPatchPayload', () => {
  it('normalizes numeric values, null unlimited, and strips unknown keys', () => {
    const payload = normalizeAdminPlanPatchPayload({
      name: 'Pro',
      price_monthly_cents: '1500' as unknown as number,
      limits_json: {
        documents_per_month: '25' as unknown as number,
        storage_bytes: '' as unknown as number,
        processing_jobs_per_month: null,
        stale_limit: 123,
      } as unknown as Record<string, number | null>,
      features_json: {
        insights_enabled: true,
        relationship_detection_enabled: false,
        stale_feature: true,
      } as unknown as Record<string, boolean>,
      is_active: true,
    });

    expect(payload).toEqual({
      name: 'Pro',
      price_monthly_cents: 1500,
      limits_json: {
        documents_per_month: 25,
        storage_bytes: null,
        processing_jobs_per_month: null,
      },
      features_json: {
        insights_enabled: true,
        relationship_detection_enabled: false,
      },
      is_active: true,
    });
  });
});
