# GraphQL Schema - My Life AI

## Overview
Schema-first GraphQL API using Strawberry (Python). Types defined here drive backend implementation and frontend code generation.

## Scalars

```graphql
scalar DateTime
scalar JSON
scalar UUID
```

## Enums

```graphql
enum EventStatus {
  SCHEDULED
  COMPLETED
  CANCELLED
}

enum EventPriority {
  NORMAL
  HIGH
  CRITICAL
}

enum NotificationType {
  IN_APP
  EMAIL
  PUSH
}

enum ConversationRole {
  USER
  ASSISTANT
  SYSTEM
  TOOL
}

enum MemoryType {
  GOAL
  PREFERENCE
  COMMITMENT
  FACT
  SUMMARY
}

enum NotificationCategory {
  REMINDER
  EVENT_CREATED
  EVENT_UPDATED
  EVENT_DELETED
  AI_SUGGESTION
  SYSTEM
}

enum CalendarView {
  MONTH
  WEEK
  DAY
  YEAR
  UPCOMING
  PAST
}

enum Theme {
  LIGHT
  DARK
  SYSTEM
}
```

## Core Types

### User
```graphql
type User {
  id: UUID!
  email: String!
  fullName: String
  avatarUrl: String
  timezone: String!
  locale: String!
  isActive: Boolean!
  isVerified: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
  settings: UserSettings!
}
```

### UserSettings
```graphql
type UserSettings {
  theme: Theme!
  calendarDefaultView: CalendarView!
  weekStartDay: Int!
  defaultReminderMinutes: [Int!]!
  notificationEmail: Boolean!
  notificationPush: Boolean!
  aiProvider: String!
  aiModel: String!
  language: String!
  dateFormat: String!
  timeFormat: String!
}
```

### Category
```graphql
type Category {
  id: UUID!
  userId: UUID!
  parentId: UUID
  name: String!
  description: String
  color: String!  # Hex #RRGGBB
  icon: String
  isSystem: Boolean!
  sortOrder: Int!
  defaultReminderMinutes: [Int!]!
  children: [Category!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type CategoryTree {
  categories: [Category!]!
  flatList: [Category!]!
}
```

### Event
```graphql
type Event {
  id: UUID!
  userId: UUID!
  category: Category
  title: String!
  description: String
  location: String
  startTime: DateTime!
  endTime: DateTime!
  allDay: Boolean!
  timezone: String!
  priority: EventPriority!
  status: EventStatus!
  isRecurring: Boolean!
  rrule: String
  rruleOriginalStart: DateTime
  recurrenceExceptions: [DateTime!]!
  preparationNotes: String
  completedAt: DateTime
  createdAt: DateTime!
  updatedAt: DateTime!
  reminders: [EventReminder!]!
}

type EventConnection {
  edges: [EventEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type EventEdge {
  node: Event!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

### EventReminder
```graphql
type EventReminder {
  id: UUID!
  eventId: UUID!
  userId: UUID!
  minutesBefore: Int!
  notificationType: NotificationType!
  isSent: Boolean!
  sentAt: DateTime
  createdAt: DateTime!
}
```

### Conversation
```graphql
type Conversation {
  id: UUID!
  userId: UUID!
  title: String
  modelProvider: String!
  modelName: String!
  systemPrompt: String
  messages: [Message!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Message {
  id: UUID!
  conversationId: UUID!
  role: ConversationRole!
  content: String!
  toolCalls: JSON
  toolCallId: String
  metadata: JSON
  createdAt: DateTime!
}
```

### UserMemory
```graphql
type UserMemory {
  id: UUID!
  userId: UUID!
  memoryType: MemoryType!
  title: String!
  content: String!
  embedding: [Float!]  # Only returned when explicitly requested
  sourceConversationId: UUID
  confidence: Float!
  isActive: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### Notification
```graphql
type Notification {
  id: UUID!
  userId: UUID!
  type: NotificationCategory!
  title: String!
  body: String
  referenceId: UUID
  referenceType: String
  isRead: Boolean!
  readAt: DateTime
  createdAt: DateTime!
}

type NotificationConnection {
  edges: [NotificationEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
  unreadCount: Int!
}

type NotificationEdge {
  node: Notification!
  cursor: String!
}
```

## Input Types

### Auth
```graphql
input RegisterInput {
  email: String!
  password: String!
  fullName: String
}

input LoginInput {
  email: String!
  password: String!
}

type AuthPayload {
  token: String!
  refreshToken: String!
  user: User!
}
```

### Category
```graphql
input CreateCategoryInput {
  parentId: UUID
  name: String!
  description: String
  color: String!
  icon: String
  defaultReminderMinutes: [Int!]
}

input UpdateCategoryInput {
  name: String
  description: String
  color: String
  icon: String
  defaultReminderMinutes: [Int!]
  sortOrder: Int
}
```

### Event
```graphql
input CreateEventInput {
  categoryId: UUID
  title: String!
  description: String
  location: String
  startTime: DateTime!
  endTime: DateTime!
  allDay: Boolean
  timezone: String!
  priority: EventPriority
  status: EventStatus
  isRecurring: Boolean
  rrule: String
  preparationNotes: String
  reminders: [CreateEventReminderInput!]
}

input UpdateEventInput {
  categoryId: UUID
  title: String
  description: String
  location: String
  startTime: DateTime
  endTime: DateTime
  allDay: Boolean
  timezone: String
  priority: EventPriority
  status: EventStatus
  preparationNotes: String
}

input CreateEventReminderInput {
  minutesBefore: Int!
  notificationType: NotificationType
}

input EventFilterInput {
  categoryIds: [UUID!]
  statuses: [EventStatus!]
  priorities: [EventPriority!]
  startDate: DateTime
  endDate: DateTime
  searchQuery: String
  isRecurring: Boolean
}
```

### Conversation
```graphql
input CreateConversationInput {
  title: String
  modelProvider: String
  modelName: String
  systemPrompt: String
}

input SendMessageInput {
  conversationId: UUID!
  content: String!
}

type SendMessagePayload {
  userMessage: Message!
  assistantMessage: Message!
}
```

### Memory
```graphql
input CreateMemoryInput {
  memoryType: MemoryType!
  title: String!
  content: String!
  sourceConversationId: UUID
  confidence: Float
}

input MemorySearchInput {
  query: String!
  memoryTypes: [MemoryType!]
  limit: Int
  threshold: Float
}
```

### Settings
```graphql
input UpdateSettingsInput {
  theme: Theme
  calendarDefaultView: CalendarView
  weekStartDay: Int
  defaultReminderMinutes: [Int!]
  notificationEmail: Boolean
  notificationPush: Boolean
  aiProvider: String
  aiModel: String
  language: String
  dateFormat: String
  timeFormat: String
}
```

### Calendar
```graphql
input CalendarRangeInput {
  startDate: DateTime!
  endDate: DateTime!
  view: CalendarView!
  timezone: String!
}
```

## Queries

```graphql
type Query {
  # Auth
  me: User
  
  # Categories
  categories: CategoryTree!
  category(id: UUID!): Category
  
  # Events
  events(filter: EventFilterInput, first: Int, after: String, last: Int, before: String): EventConnection!
  event(id: UUID!): Event
  upcomingEvents(limit: Int, days: Int): [Event!]!
  pastEvents(limit: Int, days: Int): [Event!]!
  eventsByDateRange(range: CalendarRangeInput!): [Event!]!
  recurringEventInstances(eventId: UUID!, range: CalendarRangeInput!): [Event!]!
  
  # Conversations
  conversations(first: Int, after: String): ConversationConnection!
  conversation(id: UUID!): Conversation
  
  # Memory
  memories(filter: MemoryFilterInput, first: Int, after: String): MemoryConnection!
  memory(id: UUID!): UserMemory
  searchMemory(input: MemorySearchInput!): [UserMemory!]!
  
  # Notifications
  notifications(filter: NotificationFilterInput, first: Int, after: String): NotificationConnection!
  unreadNotificationCount: Int!
  
  # Calendar
  calendarEvents(range: CalendarRangeInput!): [Event!]!
  todayEvents: [Event!]!
  thisWeekEvents: [Event!]!
  thisMonthEvents: [Event!]!
}

type ConversationConnection {
  edges: [ConversationEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type ConversationEdge {
  node: Conversation!
  cursor: String!
}

type MemoryConnection {
  edges: [MemoryEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type MemoryEdge {
  node: UserMemory!
  cursor: String!
}

input MemoryFilterInput {
  memoryTypes: [MemoryType!]
  isActive: Boolean
}

input NotificationFilterInput {
  isRead: Boolean
  types: [NotificationCategory!]
}
```

## Authentication transport

The client sends `Authorization: Bearer <accessToken>` for authenticated
requests and `X-Refresh-Token: <refreshToken>` when calling the `refreshToken`
mutation. Login and register return both tokens in `AuthPayload`.

## Mutations

```graphql
type Mutation {
  # Auth
  register(input: RegisterInput!): AuthPayload!
  login(input: LoginInput!): AuthPayload!
  logout: Boolean!
  refreshToken: String!
  verifyEmail(token: String!): Boolean!
  requestPasswordReset(email: String!): Boolean!
  resetPassword(token: String!, password: String!): Boolean!
  
  # Categories
  createCategory(input: CreateCategoryInput!): Category!
  updateCategory(id: UUID!, input: UpdateCategoryInput!): Category!
  deleteCategory(id: UUID!): Boolean!
  reorderCategories(categoryIds: [UUID!]!): [Category!]!
  
  # Events
  createEvent(input: CreateEventInput!): Event!
  updateEvent(id: UUID!, input: UpdateEventInput!): Event!
  deleteEvent(id: UUID!): Boolean!
  duplicateEvent(id: UUID!, newStartTime: DateTime!): Event!
  completeEvent(id: UUID!): Event!
  bulkCreateEvents(inputs: [CreateEventInput!]!): [Event!]!
  bulkUpdateEvents(inputs: [BulkUpdateEventInput!]!): [Event!]!
  bulkDeleteEvents(ids: [UUID!]!): Boolean!
  
  # Recurring Events
  createRecurringException(eventId: UUID!, exceptionDate: DateTime!, input: CreateEventInput!): Event!
  updateRecurringSeries(eventId: UUID!, input: UpdateEventInput!): [Event!]!
  deleteRecurringSeries(eventId: UUID!, deleteFuture: Boolean!): Boolean!
  
  # Conversations
  createConversation(input: CreateConversationInput!): Conversation!
  updateConversation(id: UUID!, title: String): Conversation!
  deleteConversation(id: UUID!): Boolean!
  sendMessage(input: SendMessageInput!): SendMessagePayload!
  streamMessage(input: SendMessageInput!): MessageStream!
  
  # Memory
  createMemory(input: CreateMemoryInput!): UserMemory!
  updateMemory(id: UUID!, input: UpdateMemoryInput!): UserMemory!
  deleteMemory(id: UUID!): Boolean!
  bulkCreateMemories(inputs: [CreateMemoryInput!]!): [UserMemory!]!
  
  # Notifications
  markNotificationRead(id: UUID!): Notification!
  markAllNotificationsRead: Boolean!
  deleteNotification(id: UUID!): Boolean!
  
  # Settings
  updateSettings(input: UpdateSettingsInput!): UserSettings!
  
  # AI Planner
  proposeEvents(conversationId: UUID!, proposal: AIEventProposalInput!): [ProposedEvent!]!
  confirmProposedEvents(conversationId: UUID!, eventIds: [UUID!]!): [Event!]!
  rejectProposedEvents(conversationId: UUID!, eventIds: [UUID!]!): Boolean!
}

input BulkUpdateEventInput {
  id: UUID!
  input: UpdateEventInput!
}

input UpdateMemoryInput {
  title: String
  content: String
  memoryType: MemoryType
  confidence: Float
  isActive: Boolean
}

input AIEventProposalInput {
  title: String!
  description: String
  suggestedDates: [DateTime!]!
  durationMinutes: Int!
  categoryId: UUID
  priority: EventPriority
  preparationNotes: String
  reminders: [CreateEventReminderInput!]
}

type ProposedEvent {
  id: UUID!  # Temporary ID for proposal
  title: String!
  description: String
  suggestedStartTime: DateTime!
  suggestedEndTime: DateTime!
  category: Category
  priority: EventPriority!
  preparationNotes: String
  reminders: [EventReminder!]!
}

type MessageStream {
  # For streaming responses
  id: UUID!
  content: String!
  done: Boolean!
}
```

## Subscriptions

```graphql
type Subscription {
  # Real-time updates
  eventCreated(userId: UUID!): Event!
  eventUpdated(userId: UUID!): Event!
  eventDeleted(userId: UUID!): UUID!
  notificationCreated(userId: UUID!): Notification!
  messageReceived(conversationId: UUID!): Message!
  reminderTriggered(userId: UUID!): EventReminder!
}
```

## Directives

```graphql
directive @auth on FIELD_DEFINITION
directive @rateLimit(max: Int!, window: String!) on FIELD_DEFINITION
directive @deprecated(reason: String) on FIELD_DEFINITION | ENUM_VALUE
```

## Error Handling

```graphql
interface Error {
  message: String!
  code: String!
}

type ValidationError implements Error {
  message: String!
  code: String!
  field: String!
  value: String
}

type AuthenticationError implements Error {
  message: String!
  code: String!
}

type AuthorizationError implements Error {
  message: String!
  code: String!
}

type NotFoundError implements Error {
  message: String!
  code: String!
  resource: String!
  id: UUID!
}

union MutationResult = Success | ValidationError | AuthenticationError | AuthorizationError | NotFoundError

type Success {
  success: Boolean!
}
```

## Pagination Conventions

- Use Relay-style cursor pagination for lists
- `first`/`after` for forward pagination
- `last`/`before` for backward pagination
- Default page size: 20, max: 100
- Return `totalCount` for UI pagination controls

## Naming Conventions

- Types: PascalCase (User, Event, Category)
- Fields: camelCase (userId, startTime, isRecurring)
- Enums: PascalCase values (SCHEDULED, HIGH)
- Inputs: PascalCase with Input suffix (CreateEventInput)
- Mutations: Verb + Noun (createEvent, updateCategory)
- Queries: Noun or Noun + Filter (events, upcomingEvents)