import { create } from 'zustand';
import { graphqlRequestWithAuth } from '@/utils/graphqlClient';

interface Notification {
  id: string;
  type: string;
  title: string;
  body?: string;
  referenceId?: string;
  referenceType?: string;
  isRead: boolean;
  readAt?: string;
  createdAt: string;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;

  fetchNotifications: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
  deleteNotification: (id: string) => Promise<void>;
  addNotification: (notification: Notification) => void;
}

const NOTIFICATIONS_QUERY = `
  query Notifications($first: Int) {
    notifications(first: $first) {
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

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  fetchNotifications: async () => {
    set({ isLoading: true });
    try {
      const response = await graphqlRequestWithAuth<{ notifications: { edges: Array<{ node: Notification }>; unreadCount: number } }>(
        NOTIFICATIONS_QUERY,
        { first: 50 }
      );

      if (response.data?.notifications) {
        const notifications = response.data.notifications.edges.map(e => e.node);
        set({
          notifications,
          unreadCount: response.data.notifications.unreadCount,
          isLoading: false,
        });
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      set({ isLoading: false });
    }
  },

  markRead: async (id: string) => {
    try {
      await graphqlRequestWithAuth(MARK_READ_MUTATION, { id });

      set(state => ({
        notifications: state.notifications.map(n =>
          n.id === id ? { ...n, isRead: true, readAt: new Date().toISOString() } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (error) {
      console.error('Failed to mark notification read:', error);
    }
  },

  markAllRead: async () => {
    try {
      await graphqlRequestWithAuth(MARK_ALL_READ_MUTATION, {});

      set(state => ({
        notifications: state.notifications.map(n => ({ ...n, isRead: true, readAt: new Date().toISOString() })),
        unreadCount: 0,
      }));
    } catch (error) {
      console.error('Failed to mark all notifications read:', error);
    }
  },

  deleteNotification: async (id: string) => {
    try {
      await graphqlRequestWithAuth(DELETE_NOTIFICATION_MUTATION, { id });

      set(state => ({
        notifications: state.notifications.filter(n => n.id !== id),
        unreadCount: state.notifications.find(n => n.id === id && !n.isRead)
          ? state.unreadCount - 1
          : state.unreadCount,
      }));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  },

  addNotification: (notification: Notification) => {
    set(state => ({
      notifications: [notification, ...state.notifications],
      unreadCount: notification.isRead ? state.unreadCount : state.unreadCount + 1,
    }));
  },
}));

export const useNotifications = () => useNotificationStore();