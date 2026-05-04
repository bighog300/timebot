import { NavLink, Outlet } from 'react-router-dom';

const settingsLinks = [
  ['/admin/settings/system', 'System'],
  ['/admin/settings/billing', 'Billing'],
  ['/admin/settings/plans', 'Plans & Limits'],
  ['/admin/settings/llm', 'LLM Providers'],
  ['/admin/settings/chatbot', 'Chatbot Defaults'],
  ['/admin/settings/prompts', 'Prompt Templates'],
  ['/admin/settings/prompts/audit', 'Prompt Audit'],
  ['/admin/settings/prompts/analytics', 'Prompt Analytics'],
  ['/admin/settings/audit', 'Audit Log'],
  ['/admin/settings/email', 'Email Providers'],
  ['/admin/settings/email/templates', 'Email Templates'],
  ['/admin/settings/email/campaigns', 'Email Campaigns'],
  ['/admin/settings/email/suppressions', 'Email Suppressions'],
  ['/admin/settings/email/logs', 'Send Logs'],
] as const;

export function AdminSettingsLayout() {
  return <div className='space-y-4'>
    <h1 className='text-xl font-semibold'>Admin Settings</h1>
    <div className='flex flex-wrap gap-2 text-sm'>
      {settingsLinks.map(([to, label]) => (
        <NavLink key={to} to={to} className='rounded border border-slate-700 px-3 py-1.5'>{label}</NavLink>
      ))}
    </div>
    <Outlet />
  </div>;
}
