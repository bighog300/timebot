import { NavLink, Outlet } from 'react-router-dom';

const links = [
  ['/settings/account', 'Account'],
  ['/settings/billing', 'Billing'],
  ['/settings/usage', 'Usage'],
] as const;

export function SettingsLayoutPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-slate-300">Manage your account, billing, and usage.</p>
      </div>
      <nav className="flex gap-2 border-b border-slate-800 pb-2">
        {links.map(([to, label]) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `rounded px-3 py-1.5 text-sm ${isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'}`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
