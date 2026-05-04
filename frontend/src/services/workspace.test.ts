import { describe, expect, it } from 'vitest';
import { getActiveWorkspaceId, setActiveWorkspaceId } from './workspace';

describe('workspace helpers', () => {
  it('uses one active workspace source', () => {
    localStorage.removeItem('activeWorkspaceId');
    setActiveWorkspaceId('ws-shared');
    expect(getActiveWorkspaceId()).toBe('ws-shared');
  });
});
