import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, vi, expect } from 'vitest';
import { AdminEmailSuppressionsPage } from '@/pages/AdminEmailSuppressionsPage';

const api = {
  listEmailSuppressions: vi.fn(async()=>[{id:'1',email:'x@example.com',reason:'manual',created_at:'now'}]),
  addEmailSuppression: vi.fn(async()=>({})),
  removeEmailSuppression: vi.fn(async()=>({})),
};
vi.mock('@/services/api', ()=>({ api }));

describe('admin suppressions page', ()=>{
  it('renders and add/remove calls API', async()=>{
    render(<AdminEmailSuppressionsPage/>);
    expect(await screen.findByText(/x@example.com/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('suppression email'), {target:{value:'z@example.com'}});
    fireEvent.click(screen.getByText('Add suppression'));
    expect(api.addEmailSuppression).toHaveBeenCalled();
    fireEvent.click(screen.getByText('Remove'));
    expect(api.removeEmailSuppression).toHaveBeenCalled();
  });
});
