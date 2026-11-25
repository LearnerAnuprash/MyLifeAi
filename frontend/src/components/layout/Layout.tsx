import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Layout as AntLayout, Avatar, Dropdown, Button } from 'antd';
import {
  CalendarOutlined,
  RobotOutlined,
  BellOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons';
import { useThemeStore } from '@/store/themeStore';
import { useAuthStore } from '@/store/authStore';
import { useNotificationStore } from '@/store/notificationStore';
import clsx from 'clsx';

const { Header, Sider, Content } = AntLayout;

type MenuItem = {
  key: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  badge?: number;
};

type UserMenuItem = {
  key: string;
  label: string;
  icon?: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  danger?: boolean;
  onClick?: () => void;
  type?: 'divider';
};

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setTheme } = useThemeStore();
  const { user, logout } = useAuthStore();
  const { unreadCount } = useNotificationStore();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
  };

  const menuItems: MenuItem[] = [
    { key: '/', icon: CalendarOutlined, label: 'Calendar' },
    { key: '/planner', icon: RobotOutlined, label: 'AI Planner' },
    { key: '/notifications', icon: BellOutlined, label: 'Notifications', badge: unreadCount > 0 ? unreadCount : undefined },
    { key: '/settings', icon: SettingOutlined, label: 'Settings' },
  ];

  const userMenuItems: UserMenuItem[] = [
    {
      key: 'profile',
      label: 'Profile',
      icon: UserOutlined,
    },
    {
      key: 'theme-light',
      label: 'Light Theme',
      icon: SunOutlined,
      onClick: () => handleThemeChange('light'),
    },
    {
      key: 'theme-dark',
      label: 'Dark Theme',
      icon: MoonOutlined,
      onClick: () => handleThemeChange('dark'),
    },
    {
      key: 'theme-system',
      label: 'System Theme',
      icon: SunOutlined,
      onClick: () => handleThemeChange('system'),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      label: 'Logout',
      icon: LogoutOutlined,
      danger: true,
      onClick: logout,
    },
  ];

  const handleNavClick = (path: string) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  const renderIcon = (IconComponent: React.ComponentType<{ className?: string; style?: React.CSSProperties }>, className?: string, style?: React.CSSProperties) => {
    return <IconComponent className={className} style={style} />;
  };

  return (
    <AntLayout className="h-screen bg-[var(--color-bg-primary)] transition-colors duration-250">
      {/* Mobile Header */}
      <Header className="lg:hidden h-16 px-4 bg-[var(--color-bg-secondary)] border-b border-[var(--color-border-primary)] flex items-center justify-between z-50">
        <Button
          type="text"
          icon={<MenuOutlined />}
          onClick={() => setMobileMenuOpen(true)}
          aria-label="Open menu"
          className="text-[var(--color-text-primary)]"
        />
        <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">My Life AI</h1>
        <div className="w-12" /> {/* Spacer for balance */}
      </Header>

      {/* Sidebar */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        breakpoint="lg"
        onBreakpoint={broken => setCollapsed(broken)}
        onCollapse={setCollapsed}
        className="bg-[var(--color-bg-secondary)] border-r border-[var(--color-border-primary)] transition-all duration-250 overflow-hidden"
        style={{ width: 280, minWidth: 280 }}
      >
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-[var(--color-border-primary)]">
            <div className="w-10 h-10 rounded-xl bg-primary-500 flex items-center justify-center flex-shrink-0">
              <CalendarOutlined className="text-white text-xl" />
            </div>
            {!collapsed && (
              <span className="text-xl font-bold text-[var(--color-text-primary)]">My Life AI</span>
            )}
          </div>

          {/* Navigation */}
          <div className="flex-1 px-3 py-4 overflow-y-auto">
            <nav className="space-y-1">
              {menuItems.map(item => (
                <NavLink
                  key={item.key}
                  to={item.key}
                  onClick={() => handleNavClick(item.key)}
                  className={({ isActive }) => clsx(
                    'flex items-center gap-3 w-full py-2 px-3 rounded-lg transition-colors',
                    isActive
                      ? 'bg-[var(--color-primary-bg)] text-[var(--color-primary-text)] font-medium'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]'
                  )}
                >
                  {renderIcon(item.icon, 'flex-shrink-0', { fontSize: 18 })}
                  {!collapsed && <span className="truncate">{item.label}</span>}
                  {item.badge && (
                    <span className="ml-auto px-2 py-0.5 text-xs font-medium bg-primary-500 text-white rounded-full">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </nav>
          </div>

          {/* User Menu */}
          <div className="px-3 pb-4 border-t border-[var(--color-border-primary)]">
            <Dropdown
              menu={{
                items: userMenuItems.map(item => {
                  if (item.type === 'divider') {
                    return { type: 'divider' as const };
                  }
                  return {
                    key: item.key ?? '',
                    label: item.label,
                    icon: item.icon ? renderIcon(item.icon) : undefined,
                    danger: item.danger,
                    onClick: item.onClick,
                  };
                }),
              }}
              placement="bottomLeft"
            >
              <Button
                type="text"
                className="w-full justify-start gap-3 px-3 py-2 rounded-lg hover:bg-[var(--color-bg-hover)] text-[var(--color-text-primary)]"
                style={{ minHeight: 'auto' }}
              >
                <Avatar
                  size={36}
                  icon={<UserOutlined />}
                  style={{
                    background: 'var(--color-primary-bg)',
                    color: 'var(--color-primary-text)',
                  }}
                />
                {!collapsed && (
                  <div className="flex-1 text-left min-w-0">
                    <p className="font-medium truncate">{user?.fullName || user?.email}</p>
                    <p className="text-xs text-[var(--color-text-tertiary)] truncate">{user?.email}</p>
                  </div>
                )}
              </Button>
            </Dropdown>
          </div>
        </div>
      </Sider>

      {/* Main Content */}
      <AntLayout className="flex-1 overflow-hidden">
        <Content className="h-full overflow-auto p-6 lg:p-8">
          <Outlet />
        </Content>
      </AntLayout>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-50 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div className="absolute inset-0 bg-black/50" />
          <div className="absolute left-0 top-0 h-full w-80 bg-[var(--color-bg-secondary)] border-r border-[var(--color-border-primary)] shadow-2xl animate-in">
            <div className="flex items-center justify-between px-4 py-4 border-b border-[var(--color-border-primary)]">
              <h2 className="text-lg font-semibold">Menu</h2>
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={(e) => { e.stopPropagation(); setMobileMenuOpen(false); }}
              />
            </div>
            <div className="p-4 space-y-1">
              {menuItems.map(item => (
                <NavLink
                  key={item.key}
                  to={item.key}
                  onClick={() => handleNavClick(item.key)}
                  className={({ isActive }) => clsx(
                    'flex items-center gap-3 w-full py-2 px-3 rounded-lg transition-colors',
                    isActive
                      ? 'bg-[var(--color-primary-bg)] text-[var(--color-primary-text)] font-medium'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]'
                  )}
                >
                  {renderIcon(item.icon, 'flex-shrink-0', { fontSize: 18 })}
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="ml-auto px-2 py-0.5 text-xs font-medium bg-primary-500 text-white rounded-full">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      )}
    </AntLayout>
  );
}