export const LOGIN_MUTATION = `
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      token
      refreshToken
      user {
        id
        email
        fullName
        avatarUrl
        timezone
        locale
        isActive
        isVerified
        createdAt
        updatedAt
        settings {
          theme
          calendarDefaultView
          weekStartDay
          defaultReminderMinutes
          notificationEmail
          notificationPush
          aiProvider
          aiModel
          language
          dateFormat
          timeFormat
        }
      }
    }
  }
`;

export const REGISTER_MUTATION = `
  mutation Register($input: RegisterInput!) {
    register(input: $input) {
      token
      refreshToken
      user {
        id
        email
        fullName
        avatarUrl
        timezone
        locale
        isActive
        isVerified
        createdAt
        updatedAt
        settings {
          theme
          calendarDefaultView
          weekStartDay
          defaultReminderMinutes
          notificationEmail
          notificationPush
          aiProvider
          aiModel
          language
          dateFormat
          timeFormat
        }
      }
    }
  }
`;

export const ME_QUERY = `
  query Me {
    me {
      id
      email
      fullName
      avatarUrl
      timezone
      locale
      isActive
      isVerified
      createdAt
      updatedAt
      settings {
        theme
        calendarDefaultView
        weekStartDay
        defaultReminderMinutes
        notificationEmail
        notificationPush
        aiProvider
        aiModel
        language
        dateFormat
        timeFormat
      }
    }
  }
`;

export const REFRESH_TOKEN_MUTATION = `
  mutation RefreshToken {
    refreshToken
  }
`;

export const CATEGORIES_QUERY = `
  query Categories {
    categories {
      categories {
        id
        userId
        parentId
        name
        description
        color
        icon
        isSystem
        sortOrder
        defaultReminderMinutes
        children {
          id
          userId
          parentId
          name
          description
          color
          icon
          isSystem
          sortOrder
          defaultReminderMinutes
          children {
            id
            name
          }
          createdAt
          updatedAt
        }
        createdAt
        updatedAt
      }
      flatList {
        id
        userId
        parentId
        name
        description
        color
        icon
        isSystem
        sortOrder
        defaultReminderMinutes
        children {
          id
          name
        }
        createdAt
        updatedAt
      }
    }
  }
`;

export const CREATE_CATEGORY_MUTATION = `
  mutation CreateCategory($input: CreateCategoryInput!) {
    createCategory(input: $input) {
      id
      userId
      parentId
      name
      description
      color
      icon
      isSystem
      sortOrder
      defaultReminderMinutes
      children { id name }
      createdAt
      updatedAt
    }
  }
`;

export const UPDATE_CATEGORY_MUTATION = `
  mutation UpdateCategory($id: UUID!, $input: UpdateCategoryInput!) {
    updateCategory(id: $id, input: $input) {
      id
      userId
      parentId
      name
      description
      color
      icon
      isSystem
      sortOrder
      defaultReminderMinutes
      children { id name }
      createdAt
      updatedAt
    }
  }
`;

export const DELETE_CATEGORY_MUTATION = `
  mutation DeleteCategory($id: UUID!) {
    deleteCategory(id: $id)
  }
`;

export const REORDER_CATEGORIES_MUTATION = `
  mutation ReorderCategories($categoryIds: [UUID!]!) {
    reorderCategories(categoryIds: $categoryIds) {
      id
      sortOrder
    }
  }
`;

export const EVENTS_BY_DATE_RANGE_QUERY = `
  query EventsByDateRange($range: CalendarRangeInput!) {
    eventsByDateRange(range: $range) {
      id
      title
      description
      location
      startTime
      endTime
      allDay
      timezone
      priority
      status
      isRecurring
      category {
        id
        name
        color
      }
    }
  }
`;

export const CREATE_EVENT_MUTATION = `
  mutation CreateEvent($input: CreateEventInput!) {
    createEvent(input: $input) {
      id
      title
      startTime
      endTime
    }
  }
`;

export const UPDATE_EVENT_MUTATION = `
  mutation UpdateEvent($id: UUID!, $input: UpdateEventInput!) {
    updateEvent(id: $id, input: $input) {
      id
    }
  }
`;

export const CONVERSATIONS_QUERY = `
  query Conversations($first: Int) {
    conversations(first: $first) {
      edges {
        node {
          id
          title
          modelProvider
          modelName
          createdAt
          updatedAt
          messages {
            id
            role
            content
            createdAt
          }
        }
      }
    }
  }
`;

export const CREATE_CONVERSATION_MUTATION = `
  mutation CreateConversation($input: CreateConversationInput!) {
    createConversation(input: $input) {
      id
      title
    }
  }
`;

export const SEND_MESSAGE_MUTATION = `
  mutation SendMessage($input: SendMessageInput!) {
    sendMessage(input: $input) {
      userMessage {
        id
        role
        content
        createdAt
      }
      assistantMessage {
        id
        role
        content
        createdAt
      }
    }
  }
`;

export const DELETE_CONVERSATION_MUTATION = `
  mutation DeleteConversation($id: UUID!) {
    deleteConversation(id: $id)
  }
`;

export const UPDATE_SETTINGS_MUTATION = `
  mutation UpdateSettings($input: UpdateSettingsInput!) {
    updateSettings(input: $input) {
      theme
      calendarDefaultView
      weekStartDay
      defaultReminderMinutes
      notificationEmail
      notificationPush
      aiProvider
      aiModel
      language
      dateFormat
      timeFormat
    }
  }
`;

export const NOTIFICATIONS_QUERY = `
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

export const MARK_NOTIFICATION_READ_MUTATION = `
  mutation MarkNotificationRead($id: UUID!) {
    markNotificationRead(id: $id) {
      id
      isRead
      readAt
    }
  }
`;

export const MARK_ALL_NOTIFICATIONS_READ_MUTATION = `
  mutation MarkAllNotificationsRead {
    markAllNotificationsRead
  }
`;

export const DELETE_NOTIFICATION_MUTATION = `
  mutation DeleteNotification($id: UUID!) {
    deleteNotification(id: $id)
  }
`;
