import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, List, Avatar, Badge, Dropdown, Menu, Space, Typography, Empty, Spin } from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  ReadOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import { graphqlRequestWithAuth } from '@/utils/graphqlClient';
import { useAuthStore } from '@/store/authStore';
import { useNotificationStore } from '@/store/notificationStore';
import { formatRelativeTime } from '@/utils/dateUtils';
import clsx from 'clsx';

const { Text } = Typography;

const NOTIFICATIONS_QUERY = `
  query Notifications($first: Int, $filter: NotificationFilterInput) {
    notifications(first: $first, filter: $filter) {
      edges {
        node {
          id
          type
          title
          body
          referenceId
          referenceType
          isRead
          readAt
          createdAt
        }
      }
      unreadCount
      totalCount
    }
  }
`;

const MARK_READ_MUTATION = `
  mutation MarkNotificationRead($id: UUID!) {
    markNotificationRead(id: $id) {
      id
      isRead
      readAt
    }
  }
`;

const MARK_ALL_READ_MUTATION = `
  mutation MarkAllNotificationsRead {
    markAllNotificationsRead
  }
`;

const DELETE_NOTIFICATION_MUTATION = `
  mutation DeleteNotification($id: UUID!) {
    deleteNotification(id: $id)
  }
`;

type Notification = {
  id: string;
  type: string;
  title: string;
  body?: string;
  referenceId?: string;
  referenceType?: string;
  isRead: boolean;
  readAt?: string;
  createdAt: string;
};

export function NotificationsPage() {
  const { user } = useAuthStore();
  const { notifications, unreadCount, fetchNotifications, markRead, markAllRead, deleteNotification } = useNotificationStore();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  // Fetch notifications on mount
  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Sync with store
  useEffect(() => {
    queryClient.setQueryData(['notifications'], notifications);
  }, [notifications, queryClient]);

  const handleMarkAllRead = async () => {
    await markAllRead();
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
  };

  const handleMarkRead = async (id: string) => {
    await markRead(id);
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await deleteNotification(id);
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'REMINDER': return <BellOutlined style={{ color: '#F59E0B' }} />;
      case 'EVENT_CREATED': return <CheckOutlined style={{ color: '#22C55E' }} />;
      case 'EVENT_UPDATED': return <CheckOutlined style={{ color: '#6366F1' }} />;
      case 'EVENT_DELETED': return <DeleteOutlined style={{ color: '#EF4444' }} />;
      case 'AI_SUGGESTION': return <BellOutlined style={{ color: '#9C27B0' }} />;
      default: return <BellOutlined style={{ color: '#6366F1' }} />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'REMINDER': return 'Reminder';
      case 'EVENT_CREATED': return 'Event Created';
      case 'EVENT_UPDATED': return 'Event Updated';
      case 'EVENT_DELETED': return 'Event Deleted';
      case 'AI_SUGGESTION': return 'AI Suggestion';
      default: return type;
    }
  };

  const filteredNotifications = filter === 'unread'
    ? notifications.filter(n => !n.isRead)
    : notifications;

  return (
    <div className="h-full flex flex-col animate-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Notifications</h1>
          <p className="text-[var(--color-text-secondary)]">Stay updated with your reminders and events</p>
        </div>

        <div className="flex items-center gap-3">
          <Dropdown
            menu={{
              items: [
                { key: 'all', label: 'All', onClick: () => setFilter('all') },
                { key: 'unread', label: 'Unread only', onClick: () => setFilter('unread') },
              ],
            }}
            placement="bottomRight"
          >
            <Button type="text" icon={<MoreOutlined />}>
              Filter: {filter === 'all' ? 'All' : 'Unread'}
            </Button>
          </Dropdown>

          {unreadCount > 0 && (
            <Button type="text" onClick={handleMarkAllRead} icon={<ReadOutlined />}>
              Mark all read
            </Button>
          )}
        </div>
      </div>

      {/* Notification List */}
      <div className="flex-1 overflow-auto">
        {filteredNotifications.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            className="h-[400px]"
          />
        ) : (
          <List
            itemLayout="horizontal"
            dataSource={filteredNotifications}
            renderItem={notification => (
              <List.Item
                className={clsx(
                  'px-4 py-3 transition-colors',
                  !notification.isRead && 'bg-[var(--color-primary-bg)]/30'
                )}
                actions={[
                  !notification.isRead && (
                    <Button
                      type="text"
                      size="small"
                      icon={<CheckOutlined />}
                      onClick={() => handleMarkRead(notification.id)}
                    >
                      Mark read
                    </Button>
                  ),
                  (
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={e => handleDelete(notification.id, e)}
                    >
                      Delete
                    </Button>
                  ),
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Avatar
                      size={40}
                      style={{
                        background: 'var(--color-primary-bg)',
                        color: 'var(--color-primary-text)',
                      }}
                    >
                      {getNotificationIcon(notification.type)}
                    </Avatar>
                  }
                  title={
                    <Space>
                      <Text strong>{notification.title}</Text>
                      <Badge status="processing" text={getTypeLabel(notification.type)} />
                      {!notification.isRead && <Badge dot color="red" />}
                    </Space>
                  }
                  description={
                    <>
                      {notification.body && (
                        <Text type="secondary" className="block mb-1">{notification.body}</Text>
                      )}
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatRelativeTime(notification.createdAt)}
                      </Text>
                    </>
                  }
                />
              </List.Item>
            )}
            pagination={false}
          />
        )}
      </div>
    </div>
  );
}

import { useState } from 'react';