// GraphQL Type Definitions (generated from schema)
// This file will be replaced by graphql-codegen output

export type UUID = string;
export type DateTime = string;
export type JSON = any;

export enum EventStatus {
  SCHEDULED = 'SCHEDULED',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
}

export enum EventPriority {
  NORMAL = 'NORMAL',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export enum NotificationType {
  IN_APP = 'IN_APP',
  EMAIL = 'EMAIL',
  PUSH = 'PUSH',
}

export enum ConversationRole {
  USER = 'USER',
  ASSISTANT = 'ASSISTANT',
  SYSTEM = 'SYSTEM',
  TOOL = 'TOOL',
}

export enum MemoryType {
  GOAL = 'GOAL',
  PREFERENCE = 'PREFERENCE',
  COMMITMENT = 'COMMITMENT',
  FACT = 'FACT',
  SUMMARY = 'SUMMARY',
}

export enum NotificationCategory {
  REMINDER = 'REMINDER',
  EVENT_CREATED = 'EVENT_CREATED',
  EVENT_UPDATED = 'EVENT_UPDATED',
  EVENT_DELETED = 'EVENT_DELETED',
  AI_SUGGESTION = 'AI_SUGGESTION',
  SYSTEM = 'SYSTEM',
}

export enum CalendarView {
  MONTH = 'MONTH',
  WEEK = 'WEEK',
  DAY = 'DAY',
  YEAR = 'YEAR',
  UPCOMING = 'UPCOMING',
  PAST = 'PAST',
}

export enum Theme {
  LIGHT = 'LIGHT',
  DARK = 'DARK',
  SYSTEM = 'SYSTEM',
}

export interface UserSettings {
  theme: Theme;
  calendarDefaultView: CalendarView;
  weekStartDay: number;
  defaultReminderMinutes: number[];
  notificationEmail: boolean;
  notificationPush: boolean;
  aiProvider: string;
  aiModel: string;
  language: string;
  dateFormat: string;
  timeFormat: string;
}

export interface User {
  id: UUID;
  email: string;
  fullName?: string;
  avatarUrl?: string;
  timezone: string;
  locale: string;
  isActive: boolean;
  isVerified: boolean;
  createdAt: DateTime;
  updatedAt: DateTime;
  settings: UserSettings;
}

export interface Category {
  id: UUID;
  userId: UUID;
  parentId?: UUID;
  name: string;
  description?: string;
  color: string;
  icon?: string;
  isSystem: boolean;
  sortOrder: number;
  defaultReminderMinutes: number[];
  children: Category[];
  createdAt: DateTime;
  updatedAt: DateTime;
}

export interface CategoryTree {
  categories: Category[];
  flatList: Category[];
}

export interface EventReminder {
  id: UUID;
  eventId: UUID;
  userId: UUID;
  minutesBefore: number;
  notificationType: NotificationType;
  isSent: boolean;
  sentAt?: DateTime;
  createdAt: DateTime;
}

export interface Event {
  id: UUID;
  userId: UUID;
  category?: Category;
  title: string;
  description?: string;
  location?: string;
  startTime: DateTime;
  endTime: DateTime;
  allDay: boolean;
  timezone: string;
  priority: EventPriority;
  status: EventStatus;
  isRecurring: boolean;
  rrule?: string;
  rruleOriginalStart?: DateTime;
  recurrenceExceptions: UUID[];
  preparationNotes?: string;
  completedAt?: DateTime;
  createdAt: DateTime;
  updatedAt: DateTime;
  reminders: EventReminder[];
}

export interface PageInfo {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor?: string;
  endCursor?: string;
}

export interface EventEdge {
  node: Event;
  cursor: string;
}

export interface EventConnection {
  edges: EventEdge[];
  pageInfo: PageInfo;
  totalCount: number;
}

export interface Message {
  id: UUID;
  conversationId: UUID;
  role: ConversationRole;
  content: string;
  toolCalls?: JSON;
  toolCallId?: string;
  metadata?: JSON;
  createdAt: DateTime;
}

export interface Conversation {
  id: UUID;
  userId: UUID;
  title?: string;
  modelProvider: string;
  modelName: string;
  systemPrompt?: string;
  messages: Message[];
  createdAt: DateTime;
  updatedAt: DateTime;
}

export interface ConversationEdge {
  node: Conversation;
  cursor: string;
}

export interface ConversationConnection {
  edges: ConversationEdge[];
  pageInfo: PageInfo;
  totalCount: number;
}

export interface UserMemory {
  id: UUID;
  userId: UUID;
  memoryType: MemoryType;
  title: string;
  content: string;
  embedding?: number[];
  sourceConversationId?: UUID;
  confidence: number;
  isActive: boolean;
  createdAt: DateTime;
  updatedAt: DateTime;
}

export interface MemoryEdge {
  node: UserMemory;
  cursor: string;
}

export interface MemoryConnection {
  edges: MemoryEdge[];
  pageInfo: PageInfo;
  totalCount: number;
}

export interface Notification {
  id: UUID;
  userId: UUID;
  type: NotificationCategory;
  title: string;
  body?: string;
  referenceId?: UUID;
  referenceType?: string;
  isRead: boolean;
  readAt?: DateTime;
  createdAt: DateTime;
}

export interface NotificationEdge {
  node: Notification;
  cursor: string;
}

export interface NotificationConnection {
  edges: NotificationEdge[];
  pageInfo: PageInfo;
  totalCount: number;
  unreadCount: number;
}

// Input Types
export interface RegisterInput {
  email: string;
  password: string;
  fullName?: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface CreateCategoryInput {
  parentId?: UUID;
  name: string;
  description?: string;
  color: string;
  icon?: string;
  defaultReminderMinutes?: number[];
}

export interface UpdateCategoryInput {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  defaultReminderMinutes?: number[];
  sortOrder?: number;
}

export interface CreateEventReminderInput {
  minutesBefore: number;
  notificationType?: NotificationType;
}

export interface CreateEventInput {
  categoryId?: UUID;
  title: string;
  description?: string;
  location?: string;
  startTime: DateTime;
  endTime: DateTime;
  allDay?: boolean;
  timezone: string;
  priority?: EventPriority;
  status?: EventStatus;
  isRecurring?: boolean;
  rrule?: string;
  preparationNotes?: string;
  reminders?: CreateEventReminderInput[];
}

export interface UpdateEventInput {
  categoryId?: UUID;
  title?: string;
  description?: string;
  location?: string;
  startTime?: DateTime;
  endTime?: DateTime;
  allDay?: boolean;
  timezone?: string;
  priority?: EventPriority;
  status?: EventStatus;
  preparationNotes?: string;
}

export interface EventFilterInput {
  categoryIds?: UUID[];
  statuses?: EventStatus[];
  priorities?: EventPriority[];
  startDate?: DateTime;
  endDate?: DateTime;
  searchQuery?: string;
  isRecurring?: boolean;
}

export interface CreateConversationInput {
  title?: string;
  modelProvider?: string;
  modelName?: string;
  systemPrompt?: string;
}

export interface SendMessageInput {
  conversationId: UUID;
  content: string;
}

export interface CreateMemoryInput {
  memoryType: MemoryType;
  title: string;
  content: string;
  sourceConversationId?: UUID;
  confidence?: number;
}

export interface UpdateMemoryInput {
  title?: string;
  content?: string;
  memoryType?: MemoryType;
  confidence?: number;
  isActive?: boolean;
}

export interface MemorySearchInput {
  query: string;
  memoryTypes?: MemoryType[];
  limit?: number;
  threshold?: number;
}

export interface MemoryFilterInput {
  memoryTypes?: MemoryType[];
  isActive?: boolean;
}

export interface UpdateSettingsInput {
  theme?: Theme;
  calendarDefaultView?: CalendarView;
  weekStartDay?: number;
  defaultReminderMinutes?: number[];
  notificationEmail?: boolean;
  notificationPush?: boolean;
  aiProvider?: string;
  aiModel?: string;
  language?: string;
  dateFormat?: string;
  timeFormat?: string;
}

export interface CalendarRangeInput {
  startDate: DateTime;
  endDate: DateTime;
  view: CalendarView;
  timezone: string;
}

export interface AIEventProposalInput {
  title: string;
  description?: string;
  suggestedDates: DateTime[];
  durationMinutes: number;
  categoryId?: UUID;
  priority?: EventPriority;
  preparationNotes?: string;
  reminders?: CreateEventReminderInput[];
}

export interface BulkUpdateEventInput {
  id: UUID;
  input: UpdateEventInput;
}

export interface NotificationFilterInput {
  isRead?: boolean;
  types?: NotificationCategory[];
}

// Payload Types
export interface AuthPayload {
  token: string;
  refreshToken: string;
  user: User;
}

export interface SendMessagePayload {
  userMessage: Message;
  assistantMessage: Message;
}

export interface ProposedEvent {
  id: UUID;
  title: string;
  description?: string;
  suggestedStartTime: DateTime;
  suggestedEndTime: DateTime;
  category?: Category;
  priority: EventPriority;
  preparationNotes?: string;
  reminders: EventReminder[];
}

export interface MutationResult {
  success?: boolean;
  message?: string;
  code?: string;
  field?: string;
  value?: string;
  resource?: string;
  id?: UUID;
}