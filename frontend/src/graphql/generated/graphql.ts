/* eslint-disable */
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** JSON object */
  Any: { input: any; output: any; }
  /** UUID string */
  UUID: { input: any; output: any; }
  /** ISO 8601 datetime string */
  datetime: { input: any; output: any; }
};

export type AiEventProposalInput = {
  categoryId?: InputMaybe<Scalars['UUID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  durationMinutes: Scalars['Int']['input'];
  preparationNotes?: InputMaybe<Scalars['String']['input']>;
  priority?: EventPriority;
  reminders?: InputMaybe<Array<CreateEventReminderInput>>;
  suggestedDates: Array<Scalars['datetime']['input']>;
  title: Scalars['String']['input'];
};

export type AuthPayload = {
  __typename: 'AuthPayload';
  token: Scalars['String']['output'];
  user: User;
};

export type BulkUpdateEventInput = {
  id: Scalars['UUID']['input'];
  input: UpdateEventInput;
};

export type CalendarRangeInput = {
  endDate: Scalars['datetime']['input'];
  startDate: Scalars['datetime']['input'];
  timezone: Scalars['String']['input'];
  view: CalendarView;
};

export enum CalendarView {
  Day = 'DAY',
  Month = 'MONTH',
  Past = 'PAST',
  Upcoming = 'UPCOMING',
  Week = 'WEEK',
  Year = 'YEAR'
}

export type Category = {
  __typename: 'Category';
  children: Array<Category>;
  color: Scalars['String']['output'];
  createdAt: Scalars['datetime']['output'];
  defaultReminderMinutes: Array<Scalars['Int']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  icon?: Maybe<Scalars['String']['output']>;
  id: Scalars['UUID']['output'];
  isSystem: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  parentId?: Maybe<Scalars['UUID']['output']>;
  sortOrder: Scalars['Int']['output'];
  updatedAt: Scalars['datetime']['output'];
  userId: Scalars['UUID']['output'];
};

export type CategoryTree = {
  __typename: 'CategoryTree';
  categories: Array<Category>;
  flatList: Array<Category>;
};

export type Conversation = {
  __typename: 'Conversation';
  createdAt: Scalars['datetime']['output'];
  id: Scalars['UUID']['output'];
  messages: Array<Message>;
  modelName: Scalars['String']['output'];
  modelProvider: Scalars['String']['output'];
  systemPrompt?: Maybe<Scalars['String']['output']>;
  title?: Maybe<Scalars['String']['output']>;
  updatedAt: Scalars['datetime']['output'];
  userId: Scalars['UUID']['output'];
};

export type ConversationConnection = {
  __typename: 'ConversationConnection';
  edges: Array<ConversationEdge>;
  pageInfo: PageInfo;
  totalCount: Scalars['Int']['output'];
};

export type ConversationEdge = {
  __typename: 'ConversationEdge';
  cursor: Scalars['String']['output'];
  node: Conversation;
};

export enum ConversationRole {
  Assistant = 'ASSISTANT',
  System = 'SYSTEM',
  Tool = 'TOOL',
  User = 'USER'
}

export type CreateCategoryInput = {
  color: Scalars['String']['input'];
  defaultReminderMinutes?: InputMaybe<Array<Scalars['Int']['input']>>;
  description?: InputMaybe<Scalars['String']['input']>;
  icon?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  parentId?: InputMaybe<Scalars['UUID']['input']>;
};

export type CreateConversationInput = {
  modelName?: InputMaybe<Scalars['String']['input']>;
  modelProvider?: InputMaybe<Scalars['String']['input']>;
  systemPrompt?: InputMaybe<Scalars['String']['input']>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export type CreateEventInput = {
  allDay?: Scalars['Boolean']['input'];
  categoryId?: InputMaybe<Scalars['UUID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  endTime: Scalars['datetime']['input'];
  isRecurring?: Scalars['Boolean']['input'];
  location?: InputMaybe<Scalars['String']['input']>;
  preparationNotes?: InputMaybe<Scalars['String']['input']>;
  priority?: EventPriority;
  reminders?: InputMaybe<Array<CreateEventReminderInput>>;
  rrule?: InputMaybe<Scalars['String']['input']>;
  startTime: Scalars['datetime']['input'];
  status?: EventStatus;
  timezone: Scalars['String']['input'];
  title: Scalars['String']['input'];
};

export type CreateEventReminderInput = {
  minutesBefore: Scalars['Int']['input'];
  notificationType?: NotificationType;
};

export type CreateMemoryInput = {
  confidence?: InputMaybe<Scalars['Float']['input']>;
  content: Scalars['String']['input'];
  memoryType: MemoryType;
  sourceConversationId?: InputMaybe<Scalars['UUID']['input']>;
  title: Scalars['String']['input'];
};

export type Event = {
  __typename: 'Event';
  allDay: Scalars['Boolean']['output'];
  category?: Maybe<Category>;
  completedAt?: Maybe<Scalars['datetime']['output']>;
  createdAt: Scalars['datetime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  endTime: Scalars['datetime']['output'];
  id: Scalars['UUID']['output'];
  isRecurring: Scalars['Boolean']['output'];
  location?: Maybe<Scalars['String']['output']>;
  preparationNotes?: Maybe<Scalars['String']['output']>;
  priority: EventPriority;
  recurrenceExceptions: Array<Scalars['UUID']['output']>;
  reminders: Array<EventReminder>;
  rrule?: Maybe<Scalars['String']['output']>;
  rruleOriginalStart?: Maybe<Scalars['datetime']['output']>;
  startTime: Scalars['datetime']['output'];
  status: EventStatus;
  timezone: Scalars['String']['output'];
  title: Scalars['String']['output'];
  updatedAt: Scalars['datetime']['output'];
  userId: Scalars['UUID']['output'];
};

export type EventConnection = {
  __typename: 'EventConnection';
  edges: Array<EventEdge>;
  pageInfo: PageInfo;
  totalCount: Scalars['Int']['output'];
};

export type EventEdge = {
  __typename: 'EventEdge';
  cursor: Scalars['String']['output'];
  node: Event;
};

export type EventFilterInput = {
  categoryIds?: InputMaybe<Array<Scalars['UUID']['input']>>;
  endDate?: InputMaybe<Scalars['datetime']['input']>;
  isRecurring?: InputMaybe<Scalars['Boolean']['input']>;
  priorities?: InputMaybe<Array<EventPriority>>;
  searchQuery?: InputMaybe<Scalars['String']['input']>;
  startDate?: InputMaybe<Scalars['datetime']['input']>;
  statuses?: InputMaybe<Array<EventStatus>>;
};

export enum EventPriority {
  Critical = 'CRITICAL',
  High = 'HIGH',
  Normal = 'NORMAL'
}

export type EventReminder = {
  __typename: 'EventReminder';
  createdAt: Scalars['datetime']['output'];
  eventId: Scalars['UUID']['output'];
  id: Scalars['UUID']['output'];
  isSent: Scalars['Boolean']['output'];
  minutesBefore: Scalars['Int']['output'];
  notificationType: NotificationType;
  sentAt?: Maybe<Scalars['datetime']['output']>;
  userId: Scalars['UUID']['output'];
};

export enum EventStatus {
  Cancelled = 'CANCELLED',
  Completed = 'COMPLETED',
  Scheduled = 'SCHEDULED'
}

export type LoginInput = {
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
};

export type MemoryConnection = {
  __typename: 'MemoryConnection';
  edges: Array<MemoryEdge>;
  pageInfo: PageInfo;
  totalCount: Scalars['Int']['output'];
};

export type MemoryEdge = {
  __typename: 'MemoryEdge';
  cursor: Scalars['String']['output'];
  node: UserMemory;
};

export type MemoryFilterInput = {
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  memoryTypes?: InputMaybe<Array<MemoryType>>;
};

export type MemorySearchInput = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  memoryTypes?: InputMaybe<Array<MemoryType>>;
  query: Scalars['String']['input'];
  threshold?: InputMaybe<Scalars['Float']['input']>;
};

export enum MemoryType {
  Commitment = 'COMMITMENT',
  Fact = 'FACT',
  Goal = 'GOAL',
  Preference = 'PREFERENCE',
  Summary = 'SUMMARY'
}

export type Message = {
  __typename: 'Message';
  content: Scalars['String']['output'];
  conversationId: Scalars['UUID']['output'];
  createdAt: Scalars['datetime']['output'];
  id: Scalars['UUID']['output'];
  metadata?: Maybe<Scalars['Any']['output']>;
  role: ConversationRole;
  toolCallId?: Maybe<Scalars['String']['output']>;
  toolCalls?: Maybe<Scalars['Any']['output']>;
};

export type Mutation = {
  __typename: 'Mutation';
  bulkCreateEvents: Array<Event>;
  bulkCreateMemories: Array<UserMemory>;
  bulkDeleteEvents: Scalars['Boolean']['output'];
  bulkUpdateEvents: Array<Event>;
  completeEvent: Event;
  confirmProposedEvents: Array<Event>;
  createCategory: Category;
  createConversation: Conversation;
  createEvent: Event;
  createMemory: UserMemory;
  createRecurringException: Event;
  deleteCategory: Scalars['Boolean']['output'];
  deleteConversation: Scalars['Boolean']['output'];
  deleteEvent: Scalars['Boolean']['output'];
  deleteMemory: Scalars['Boolean']['output'];
  deleteNotification: Scalars['Boolean']['output'];
  deleteRecurringSeries: Scalars['Boolean']['output'];
  duplicateEvent: Event;
  login: AuthPayload;
  logout: Scalars['Boolean']['output'];
  markAllNotificationsRead: Scalars['Boolean']['output'];
  markNotificationRead: Notification;
  proposeEvents: Array<ProposedEvent>;
  refreshToken: Scalars['String']['output'];
  register: AuthPayload;
  rejectProposedEvents: Scalars['Boolean']['output'];
  reorderCategories: Array<Category>;
  requestPasswordReset: Scalars['Boolean']['output'];
  resetPassword: Scalars['Boolean']['output'];
  sendMessage: SendMessagePayload;
  updateCategory: Category;
  updateConversation: Conversation;
  updateEvent: Event;
  updateMemory: UserMemory;
  updateRecurringSeries: Event;
  updateSettings: UserSettings;
  verifyEmail: Scalars['Boolean']['output'];
};


export type MutationBulkCreateEventsArgs = {
  inputs: Array<CreateEventInput>;
};


export type MutationBulkCreateMemoriesArgs = {
  inputs: Array<CreateMemoryInput>;
};


export type MutationBulkDeleteEventsArgs = {
  ids: Array<Scalars['UUID']['input']>;
};


export type MutationBulkUpdateEventsArgs = {
  inputs: Array<BulkUpdateEventInput>;
};


export type MutationCompleteEventArgs = {
  id: Scalars['UUID']['input'];
};


export type MutationConfirmProposedEventsArgs = {
  conversationId: Scalars['UUID']['input'];
  eventIds: Array<Scalars['UUID']['input']>;
};


export type MutationCreateCategoryArgs = {
  input: CreateCategoryInput;
};


export type MutationCreateConversationArgs = {
  input: CreateConversationInput;
};


export type MutationCreateEventArgs = {
  input: CreateEventInput;
};


export type MutationCreateMemoryArgs = {
  input: CreateMemoryInput;
};


export type MutationCreateRecurringExceptionArgs = {
  eventId: Scalars['UUID']['input'];
  exceptionDate: Scalars['datetime']['input'];
  input: CreateEventInput;
};


export type MutationDeleteCategoryArgs = {
  id: Scalars['UUID']['input'];
};


export type MutationDeleteConversationArgs = {
  id: Scalars['UUID']['input'];
};


export type MutationDeleteEventArgs = {
  id: Scalars['UUID']['input'];
};


export type MutationDeleteMemoryArgs = {
  id: Scalars['UUID']['input'];
};


export type MutationDeleteNotificationArgs = {
  id: Scalars['UUID']['input'];
};


export type MutationDeleteRecurringSeriesArgs = {
  deleteFuture?: Scalars['Boolean']['input'];
  eventId: Scalars['UUID']['input'];
};


export type MutationDuplicateEventArgs = {
  id: Scalars['UUID']['input'];
  newStartTime: Scalars['datetime']['input'];
};


export type MutationLoginArgs = {
  input: LoginInput;
};


export type MutationMarkNotificationReadArgs = {
  id: Scalars['UUID']['input'];
};


export type MutationProposeEventsArgs = {
  conversationId: Scalars['UUID']['input'];
  proposal: AiEventProposalInput;
};


export type MutationRegisterArgs = {
  input: RegisterInput;
};


export type MutationRejectProposedEventsArgs = {
  conversationId: Scalars['UUID']['input'];
  eventIds: Array<Scalars['UUID']['input']>;
};


export type MutationReorderCategoriesArgs = {
  categoryIds: Array<Scalars['UUID']['input']>;
};


export type MutationRequestPasswordResetArgs = {
  email: Scalars['String']['input'];
};


export type MutationResetPasswordArgs = {
  password: Scalars['String']['input'];
  token: Scalars['String']['input'];
};


export type MutationSendMessageArgs = {
  input: SendMessageInput;
};


export type MutationUpdateCategoryArgs = {
  id: Scalars['UUID']['input'];
  input: UpdateCategoryInput;
};


export type MutationUpdateConversationArgs = {
  id: Scalars['UUID']['input'];
  title?: InputMaybe<Scalars['String']['input']>;
};


export type MutationUpdateEventArgs = {
  id: Scalars['UUID']['input'];
  input: UpdateEventInput;
};


export type MutationUpdateMemoryArgs = {
  id: Scalars['UUID']['input'];
  input: UpdateMemoryInput;
};


export type MutationUpdateRecurringSeriesArgs = {
  eventId: Scalars['UUID']['input'];
  input: UpdateEventInput;
};


export type MutationUpdateSettingsArgs = {
  input: UpdateSettingsInput;
};


export type MutationVerifyEmailArgs = {
  token: Scalars['String']['input'];
};

export type Notification = {
  __typename: 'Notification';
  body?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['datetime']['output'];
  id: Scalars['UUID']['output'];
  isRead: Scalars['Boolean']['output'];
  readAt?: Maybe<Scalars['datetime']['output']>;
  referenceId?: Maybe<Scalars['UUID']['output']>;
  referenceType?: Maybe<Scalars['String']['output']>;
  title: Scalars['String']['output'];
  type: NotificationCategory;
  userId: Scalars['UUID']['output'];
};

export enum NotificationCategory {
  AiSuggestion = 'AI_SUGGESTION',
  EventCreated = 'EVENT_CREATED',
  EventDeleted = 'EVENT_DELETED',
  EventUpdated = 'EVENT_UPDATED',
  Reminder = 'REMINDER',
  System = 'SYSTEM'
}

export type NotificationConnection = {
  __typename: 'NotificationConnection';
  edges: Array<NotificationEdge>;
  pageInfo: PageInfo;
  totalCount: Scalars['Int']['output'];
  unreadCount: Scalars['Int']['output'];
};

export type NotificationEdge = {
  __typename: 'NotificationEdge';
  cursor: Scalars['String']['output'];
  node: Notification;
};

export type NotificationFilterInput = {
  isRead?: InputMaybe<Scalars['Boolean']['input']>;
  types?: InputMaybe<Array<NotificationCategory>>;
};

export enum NotificationType {
  Email = 'EMAIL',
  InApp = 'IN_APP',
  Push = 'PUSH'
}

export type PageInfo = {
  __typename: 'PageInfo';
  endCursor?: Maybe<Scalars['String']['output']>;
  hasNextPage: Scalars['Boolean']['output'];
  hasPreviousPage: Scalars['Boolean']['output'];
  startCursor?: Maybe<Scalars['String']['output']>;
};

export type ProposedEvent = {
  __typename: 'ProposedEvent';
  category?: Maybe<Category>;
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['UUID']['output'];
  preparationNotes?: Maybe<Scalars['String']['output']>;
  priority: EventPriority;
  reminders: Array<EventReminder>;
  suggestedEndTime: Scalars['datetime']['output'];
  suggestedStartTime: Scalars['datetime']['output'];
  title: Scalars['String']['output'];
};

export type Query = {
  __typename: 'Query';
  calendarEvents: Array<Event>;
  categories: CategoryTree;
  category?: Maybe<Category>;
  conversation?: Maybe<Conversation>;
  conversations: ConversationConnection;
  event?: Maybe<Event>;
  events: EventConnection;
  eventsByDateRange: Array<Event>;
  me?: Maybe<User>;
  memories: MemoryConnection;
  memory?: Maybe<UserMemory>;
  notifications: NotificationConnection;
  pastEvents: Array<Event>;
  recurringEventInstances: Array<Event>;
  searchMemory: Array<UserMemory>;
  thisMonthEvents: Array<Event>;
  thisWeekEvents: Array<Event>;
  todayEvents: Array<Event>;
  unreadNotificationCount: Scalars['Int']['output'];
  upcomingEvents: Array<Event>;
};


export type QueryCalendarEventsArgs = {
  range: CalendarRangeInput;
};


export type QueryCategoryArgs = {
  id: Scalars['UUID']['input'];
};


export type QueryConversationArgs = {
  id: Scalars['UUID']['input'];
};


export type QueryConversationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: Scalars['Int']['input'];
};


export type QueryEventArgs = {
  id: Scalars['UUID']['input'];
};


export type QueryEventsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<EventFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryEventsByDateRangeArgs = {
  range: CalendarRangeInput;
};


export type QueryMemoriesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<MemoryFilterInput>;
  first?: Scalars['Int']['input'];
};


export type QueryMemoryArgs = {
  id: Scalars['UUID']['input'];
};


export type QueryNotificationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<NotificationFilterInput>;
  first?: Scalars['Int']['input'];
};


export type QueryPastEventsArgs = {
  days?: Scalars['Int']['input'];
  limit?: Scalars['Int']['input'];
};


export type QueryRecurringEventInstancesArgs = {
  eventId: Scalars['UUID']['input'];
  range: CalendarRangeInput;
};


export type QuerySearchMemoryArgs = {
  input: MemorySearchInput;
};


export type QueryUpcomingEventsArgs = {
  days?: Scalars['Int']['input'];
  limit?: Scalars['Int']['input'];
};

export type RegisterInput = {
  email: Scalars['String']['input'];
  fullName?: InputMaybe<Scalars['String']['input']>;
  password: Scalars['String']['input'];
};

export type SendMessageInput = {
  content: Scalars['String']['input'];
  conversationId: Scalars['UUID']['input'];
};

export type SendMessagePayload = {
  __typename: 'SendMessagePayload';
  assistantMessage: Message;
  userMessage: Message;
};

export type Subscription = {
  __typename: 'Subscription';
  eventCreated: Event;
  eventDeleted: Scalars['UUID']['output'];
  eventUpdated: Event;
  messageReceived: Message;
  notificationCreated: Notification;
  reminderTriggered: EventReminder;
};


export type SubscriptionEventCreatedArgs = {
  userId: Scalars['UUID']['input'];
};


export type SubscriptionEventDeletedArgs = {
  userId: Scalars['UUID']['input'];
};


export type SubscriptionEventUpdatedArgs = {
  userId: Scalars['UUID']['input'];
};


export type SubscriptionMessageReceivedArgs = {
  conversationId: Scalars['UUID']['input'];
};


export type SubscriptionNotificationCreatedArgs = {
  userId: Scalars['UUID']['input'];
};


export type SubscriptionReminderTriggeredArgs = {
  userId: Scalars['UUID']['input'];
};

export enum Theme {
  Dark = 'DARK',
  Light = 'LIGHT',
  System = 'SYSTEM'
}

export type UpdateCategoryInput = {
  color?: InputMaybe<Scalars['String']['input']>;
  defaultReminderMinutes?: InputMaybe<Array<Scalars['Int']['input']>>;
  description?: InputMaybe<Scalars['String']['input']>;
  icon?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  sortOrder?: InputMaybe<Scalars['Int']['input']>;
};

export type UpdateEventInput = {
  allDay?: InputMaybe<Scalars['Boolean']['input']>;
  categoryId?: InputMaybe<Scalars['UUID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  endTime?: InputMaybe<Scalars['datetime']['input']>;
  location?: InputMaybe<Scalars['String']['input']>;
  preparationNotes?: InputMaybe<Scalars['String']['input']>;
  priority?: InputMaybe<EventPriority>;
  startTime?: InputMaybe<Scalars['datetime']['input']>;
  status?: InputMaybe<EventStatus>;
  timezone?: InputMaybe<Scalars['String']['input']>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateMemoryInput = {
  confidence?: InputMaybe<Scalars['Float']['input']>;
  content?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  memoryType?: InputMaybe<MemoryType>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateSettingsInput = {
  aiModel?: InputMaybe<Scalars['String']['input']>;
  aiProvider?: InputMaybe<Scalars['String']['input']>;
  calendarDefaultView?: InputMaybe<CalendarView>;
  dateFormat?: InputMaybe<Scalars['String']['input']>;
  defaultReminderMinutes?: InputMaybe<Array<Scalars['Int']['input']>>;
  language?: InputMaybe<Scalars['String']['input']>;
  notificationEmail?: InputMaybe<Scalars['Boolean']['input']>;
  notificationPush?: InputMaybe<Scalars['Boolean']['input']>;
  theme?: InputMaybe<Theme>;
  timeFormat?: InputMaybe<Scalars['String']['input']>;
  weekStartDay?: InputMaybe<Scalars['Int']['input']>;
};

export type User = {
  __typename: 'User';
  avatarUrl?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['datetime']['output'];
  email: Scalars['String']['output'];
  fullName?: Maybe<Scalars['String']['output']>;
  id: Scalars['UUID']['output'];
  isActive: Scalars['Boolean']['output'];
  isVerified: Scalars['Boolean']['output'];
  locale: Scalars['String']['output'];
  settings: UserSettings;
  timezone: Scalars['String']['output'];
  updatedAt: Scalars['datetime']['output'];
};

export type UserMemory = {
  __typename: 'UserMemory';
  confidence: Scalars['Float']['output'];
  content: Scalars['String']['output'];
  createdAt: Scalars['datetime']['output'];
  embedding?: Maybe<Array<Scalars['Float']['output']>>;
  id: Scalars['UUID']['output'];
  isActive: Scalars['Boolean']['output'];
  memoryType: MemoryType;
  sourceConversationId?: Maybe<Scalars['UUID']['output']>;
  title: Scalars['String']['output'];
  updatedAt: Scalars['datetime']['output'];
  userId: Scalars['UUID']['output'];
};

export type UserSettings = {
  __typename: 'UserSettings';
  aiModel: Scalars['String']['output'];
  aiProvider: Scalars['String']['output'];
  calendarDefaultView: CalendarView;
  dateFormat: Scalars['String']['output'];
  defaultReminderMinutes: Array<Scalars['Int']['output']>;
  language: Scalars['String']['output'];
  notificationEmail: Scalars['Boolean']['output'];
  notificationPush: Scalars['Boolean']['output'];
  theme: Theme;
  timeFormat: Scalars['String']['output'];
  weekStartDay: Scalars['Int']['output'];
};
