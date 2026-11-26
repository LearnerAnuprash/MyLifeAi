import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, Dropdown, Modal, Form, Input, Select, DatePicker, Radio, message } from 'antd';
import type { FormInstance } from 'antd';
import {
  PlusOutlined,
  LeftOutlined,
  RightOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, addMonths, subMonths, addDays, isSameDay, isSameMonth, isToday, parseISO, startOfDay, endOfDay } from 'date-fns';
import dayjs from 'dayjs';
import { graphqlRequestWithAuth } from '@/utils/graphqlClient';
import { useAuthStore } from '@/store/authStore';
import { useCategoryStore } from '@/store/categoryStore';
import clsx from 'clsx';
import { RecurrenceEditor } from '@/components/events';
import { EVENTS_BY_DATE_RANGE_QUERY, CREATE_EVENT_MUTATION, UPDATE_EVENT_MUTATION } from "@/graphql/operations";

type Event = {
  id: string;
  title: string;
  description?: string;
  location?: string;
  startTime: string;
  endTime: string;
  allDay: boolean;
  timezone: string;
  priority: 'NORMAL' | 'HIGH' | 'CRITICAL';
  status: 'SCHEDULED' | 'COMPLETED' | 'CANCELLED';
  isRecurring: boolean;
  category?: { id: string; name: string; color: string };
};

type CalendarView = 'month' | 'week' | 'day';

export function CalendarPage() {
  const { user } = useAuthStore();
  const { categories } = useCategoryStore();
  const queryClient = useQueryClient();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('month');
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [eventModalOpen, setEventModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [form] = Form.useForm();

  // Fetch events for current view
  const { data: eventsData, isLoading } = useQuery({
    queryKey: ['events', view, currentDate],
    queryFn: async () => {
      const { start, end } = getDateRange(view, currentDate);
      const response = await graphqlRequestWithAuth<{ eventsByDateRange: Event[] }>(EVENTS_BY_DATE_RANGE_QUERY, {
        range: { startDate: start.toISOString(), endDate: end.toISOString(), view: view.toUpperCase(), timezone: user?.timezone || 'UTC' },
      });
      return response.data?.eventsByDateRange || [];
    },
    enabled: !!user,
  });

  const events = eventsData || [];

  // Mutations
  interface CreateEventInput {
    title: string;
    startTime: string;
    endTime: string;
    timezone: string;
    categoryId?: string;
    description?: string;
    location?: string;
    allDay?: boolean;
    priority?: 'NORMAL' | 'HIGH' | 'CRITICAL';
    isRecurring?: boolean;
    rrule?: string;
    preparationNotes?: string;
  }

  interface UpdateEventInput {
    title?: string;
    startTime?: string;
    endTime?: string;
    timezone?: string;
    categoryId?: string;
    description?: string;
    location?: string;
    allDay?: boolean;
    priority?: 'NORMAL' | 'HIGH' | 'CRITICAL';
    preparationNotes?: string;
  }

  interface EventResponse {
    id: string;
    title: string;
    startTime: string;
    endTime: string;
  }

  const createEventMutation = useMutation<EventResponse, Error, CreateEventInput>({
    mutationFn: async (input) => {
      const response = await graphqlRequestWithAuth<{ createEvent: EventResponse }>(CREATE_EVENT_MUTATION, { input });
      const event = response.data?.createEvent;
      if (!event) throw new Error("Failed to create event");
      return event;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      message.success('Event created');
      closeEventModal();
    },
    onError: (error: Error) => message.error(error.message),
  });

  const updateEventMutation = useMutation<EventResponse, Error, { id: string; input: UpdateEventInput }>({
    mutationFn: async ({ id, input }) => {
      const response = await graphqlRequestWithAuth<{ updateEvent: EventResponse }>(UPDATE_EVENT_MUTATION, { id, input });
      const event = response.data?.updateEvent;
      if (!event) throw new Error("Failed to update event");
      return event;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      message.success('Event updated');
      closeEventModal();
    },
    onError: (error: Error) => message.error(error.message),
  });




  // Navigation
  const goToToday = () => setCurrentDate(new Date());
  const goToPrevious = () => {
    setCurrentDate(prev => {
      switch (view) {
        case 'month': return subMonths(prev, 1);
        case 'week': return addWeeks(prev, -1);
        case 'day': return addDays(prev, -1);
      }
    });
  };
  const goToNext = () => {
    setCurrentDate(prev => {
      switch (view) {
        case 'month': return addMonths(prev, 1);
        case 'week': return addWeeks(prev, 1);
        case 'day': return addDays(prev, 1);
      }
    });
  };

  // Event handlers
  const openCreateEvent = (date?: Date) => {
    setIsEditing(false);
    form.resetFields();
    const start = date ? dayjs(date) : dayjs();
    const end = date ? dayjs(date).add(1, 'hour') : dayjs().add(1, 'hour');
    form.setFieldsValue({
      startTime: start,
      endTime: end,
      allDay: false,
      priority: 'NORMAL',
      status: 'SCHEDULED',
      timezone: user?.timezone || 'UTC',
    });
    setEventModalOpen(true);
  };

  const openEditEvent = (event: Event) => {
    setSelectedEvent(event);
    setIsEditing(true);
    form.setFieldsValue({
      title: event.title,
      description: event.description,
      location: event.location,
      startTime: dayjs(event.startTime),
      endTime: dayjs(event.endTime),
      allDay: event.allDay,
      categoryId: event.category?.id,
      priority: event.priority,
      status: event.status,
      timezone: event.timezone,
      preparationNotes: '', // Would come from event
      recurrence: event.isRecurring ? { rrule: '', recurrenceEnd: '', recurrenceEndType: 'never' } : undefined,
    });
    setEventModalOpen(true);
  };

  const closeEventModal = () => {
    setEventModalOpen(false);
    setSelectedEvent(null);
    setIsEditing(false);
    form.resetFields();
  };

  const handleEventSubmit = async (values: any) => {
    const input: any = {
      title: values.title,
      description: values.description,
      location: values.location,
      startTime: values.startTime?.toISOString?.() || values.startTime,
      endTime: values.endTime?.toISOString?.() || values.endTime,
      allDay: values.allDay,
      categoryId: values.categoryId,
      priority: values.priority,
      status: values.status,
      timezone: values.timezone,
      preparationNotes: values.preparationNotes,
    };

    // Handle recurrence fields
    if (values.recurrence && values.recurrence.rrule) {
      input.rrule = values.recurrence.rrule;
      input.recurrenceEnd = values.recurrence.recurrenceEnd;
      input.recurrenceEndType = values.recurrence.recurrenceEndType;
    }

    if (isEditing && selectedEvent) {
      await updateEventMutation.mutateAsync({ id: selectedEvent.id, input });
    } else {
      await createEventMutation.mutateAsync(input);
    }
  };

  // Render
  const monthWeeks = getMonthWeeks(currentDate);
  const weekDays = getWeekDays(currentDate);
  const dayHours = generateDayHours();

  const eventsByDay = groupEventsByDay(events);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 animate-in">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            {format(currentDate, view === 'month' ? 'MMMM yyyy' : view === 'week' ? "'Week of' MMM d, yyyy" : 'EEEE, MMMM d, yyyy')}
          </h1>
          <p className="text-[var(--color-text-secondary)]">
            {view === 'month' ? 'Monthly view' : view === 'week' ? 'Weekly view' : 'Daily view'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Dropdown
            menu={{
              items: [
                { key: 'month', label: 'Month', icon: <CalendarOutlined />, onClick: () => setView('month') },
                { key: 'week', label: 'Week', icon: <CalendarOutlined />, onClick: () => setView('week') },
                { key: 'day', label: 'Day', icon: <CalendarOutlined />, onClick: () => setView('day') },
              ],
            }}
            placement="bottomRight"
          >
            <Button type="text" icon={<CalendarOutlined />} className="hidden sm:flex">
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </Button>
          </Dropdown>

          <Button type="text" icon={<LeftOutlined />} onClick={goToPrevious} aria-label="Previous" />
          <Button type="text" icon={<RightOutlined />} onClick={goToNext} aria-label="Next" />
          <Button type="text" icon={<ClockCircleOutlined />} onClick={goToToday}>
            Today
          </Button>

          <Button type="primary" icon={<PlusOutlined />} onClick={() => openCreateEvent()}>
            New Event
          </Button>
        </div>
      </div>

      {/* Calendar */}
      <div className="flex-1 overflow-auto">
        {view === 'month' && (
          <MonthCalendar
            weeks={monthWeeks}
            currentDate={currentDate}
            eventsByDay={eventsByDay}
            onDayClick={openCreateEvent}
            onEventClick={openEditEvent}
            isLoading={isLoading}
          />
        )}

        {view === 'week' && (
          <WeekCalendar
            days={weekDays}
            hours={dayHours}
            events={events}
            onSlotClick={openCreateEvent}
            onEventClick={openEditEvent}
            isLoading={isLoading}
          />
        )}

        {view === 'day' && (
          <DayCalendar
            date={currentDate}
            hours={dayHours}
            events={events.filter(e => isSameDay(parseISO(e.startTime), currentDate))}
            onSlotClick={openCreateEvent}
            onEventClick={openEditEvent}
            isLoading={isLoading}
          />
        )}
      </div>

      {/* Event Modal */}
      <EventModal
        open={eventModalOpen}
        onClose={closeEventModal}
        form={form}
        isEditing={isEditing}
        categories={categories as EventModalCategory[]}
        userTimezone={user?.timezone || 'UTC'}
        onSubmit={handleEventSubmit}
        submitting={createEventMutation.isPending || updateEventMutation.isPending}
      />
    </div>
  );
}

// Helper functions
function getDateRange(view: CalendarView, date: Date) {
  const timezone = 'UTC';
  switch (view) {
    case 'month': {
      const start = startOfMonth(date);
      const end = endOfMonth(endOfWeek(endOfMonth(date)));
      return { start, end, timezone };
    }
    case 'week': {
      const start = startOfWeek(date, { weekStartsOn: 0 });
      const end = endOfWeek(date, { weekStartsOn: 0 });
      return { start, end, timezone };
    }
    case 'day': {
      const start = startOfDay(date);
      const end = endOfDay(date);
      return { start, end, timezone };
    }
  }
}

function addWeeks(date: Date, weeks: number): Date {
  return addDays(date, weeks * 7);
}

function addHours(date: Date, hours: number): Date {
  const d = new Date(date);
  d.setHours(d.getHours() + hours);
  return d;
}

function getMonthWeeks(date: Date): Date[][] {
  const monthStart = startOfMonth(date);
  const monthEnd = endOfMonth(date);
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 0 });
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 0 });

  const weeks: Date[][] = [];
  let current = calendarStart;

  while (current <= calendarEnd) {
    const week: Date[] = [];
    for (let i = 0; i < 7; i++) {
      week.push(addDays(current, i));
    }
    weeks.push(week);
    current = addWeeks(current, 1);
  }

  return weeks;
}

function getWeekDays(date: Date): Date[] {
  const weekStart = startOfWeek(date, { weekStartsOn: 0 });
  return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
}

function generateDayHours(): Date[] {
  const hours: Date[] = [];
  const base = new Date();
  base.setHours(0, 0, 0, 0);
  for (let h = 0; h < 24; h++) {
    const d = new Date(base);
    d.setHours(h);
    hours.push(d);
  }
  return hours;
}

function groupEventsByDay(events: Event[]): Map<string, Event[]> {
  const map = new Map<string, Event[]>();
  events.forEach(event => {
    const dayKey = format(parseISO(event.startTime), 'yyyy-MM-dd');
    if (!map.has(dayKey)) map.set(dayKey, []);
    map.get(dayKey)!.push(event);
  });
  return map;
}

// Calendar Components
function MonthCalendar({ weeks, currentDate, eventsByDay, onDayClick, onEventClick, isLoading }: {
  weeks: Date[][];
  currentDate: Date;
  eventsByDay: Map<string, Event[]>;
  onDayClick: (day: Date) => void;
  onEventClick: (event: Event) => void;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="calendar-grid rounded-xl overflow-hidden bg-[var(--color-bg-secondary)]">
      {/* Day Headers */}
      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, i) => (
        <div key={i} className="p-3 text-center font-semibold text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] border-b border-[var(--color-border-primary)]">
          {day}
        </div>
      ))}

      {/* Weeks */}
      {weeks.map((week, weekIndex) =>
        week.map((day, dayIndex) => {
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isTodayFlag = isToday(day);
          const dayKey = format(day, 'yyyy-MM-dd');
          const dayEvents = eventsByDay.get(dayKey) || [];
          const displayEvents = dayEvents.slice(0, 3);
          const moreCount = dayEvents.length - 3;

          return (
            <div
              key={`${weekIndex}-${dayIndex}`}
              className={clsx(
                'calendar-day relative',
                !isCurrentMonth && 'other-month',
                isTodayFlag && 'today'
              )}
              onClick={() => onDayClick(day)}
            >
              <span className={clsx('calendar-day-number', isTodayFlag && 'text-primary-600')}>
                {format(day, 'd')}
              </span>

              <div className="space-y-1 mt-1">
                {displayEvents.map(event => (
                  <EventChip key={event.id} event={event} onClick={(e) => { e.stopPropagation(); onEventClick(event); }} />
                ))}

                {moreCount > 0 && (
                  <div className="event-more" onClick={(e) => { e.stopPropagation(); onDayClick(day); }}>
                    +{moreCount} more
                  </div>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

function WeekCalendar({ days, hours, events, onSlotClick, onEventClick, isLoading }: {
  days: Date[];
  hours: Date[];
  events: Event[];
  onSlotClick: (date: Date) => void;
  onEventClick: (event: Event) => void;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  const eventsByDay = groupEventsByDay(events);

  return (
    <div className="week-view rounded-xl overflow-hidden bg-[var(--color-bg-secondary)] h-[700px]">
      {/* Time column header */}
      <div className="week-time-column border-b border-[var(--color-border-primary)]">
        <div className="text-center text-xs text-[var(--color-text-tertiary)]">Time</div>
      </div>

      {/* Day headers */}
      {days.map((day, i) => (
        <div key={i} className={clsx('week-day-header', isToday(day) && 'today')}>
          <div className="text-sm text-[var(--color-text-tertiary)]">{format(day, 'EEE')}</div>
          <div className={clsx('text-xl font-bold', isToday(day) && 'text-primary-600')}>
            {format(day, 'd')}
          </div>
        </div>
      ))}

      {/* Time slots */}
      {hours.map((hour, hourIndex) => (
        <div key={hourIndex} className="flex">
          <div className="week-time-column border-b border-[var(--color-border-primary)]">
            {hourIndex % 2 === 0 && format(hour, 'ha')}
          </div>
          {days.map((day, dayIndex) => {
            const dayKey = format(day, 'yyyy-MM-dd');
            const dayEvents = eventsByDay.get(dayKey) || [];
            const slotEvents = dayEvents.filter(event => {
              const start = parseISO(event.startTime);
              const end = parseISO(event.endTime);
              return start < addHours(hour, 1) && end > hour;
            });

            return (
              <div
                key={dayIndex}
                className="week-day-column relative border-b border-[var(--color-border-primary)]"
                onClick={() => onSlotClick(hour)}
              >
                {slotEvents.map(event => (
                  <WeekEventChip
                    key={event.id}
                    event={event}
                    hour={hour}
                    onClick={(e) => { e.stopPropagation(); onEventClick(event); }}
                  />
                ))}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function DayCalendar({ date, hours, events, onSlotClick, onEventClick, isLoading }: {
  date: Date;
  hours: Date[];
  events: Event[];
  onSlotClick: (date: Date) => void;
  onEventClick: (event: Event) => void;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="week-view rounded-xl overflow-hidden bg-[var(--color-bg-secondary)] h-[700px] max-w-4xl mx-auto">
      <div className="week-time-column border-b border-[var(--color-border-primary)]">
        <div className="text-center text-xs text-[var(--color-text-tertiary)]">Time</div>
      </div>

      <div className={clsx('week-day-header today', 'flex-1')}>
        <div className="text-sm text-primary-600">{format(date, 'EEE')}</div>
        <div className="text-xl font-bold text-primary-600">{format(date, 'MMMM d, yyyy')}</div>
      </div>

      {hours.map((hour, hourIndex) => (
        <div key={hourIndex} className="flex">
          <div className="week-time-column border-b border-[var(--color-border-primary)]">
            {hourIndex % 2 === 0 && format(hour, 'ha')}
          </div>
          <div
            className="week-day-column relative border-b border-[var(--color-border-primary)] flex-1"
            onClick={() => onSlotClick(hour)}
          >
            {events
              .filter(event => {
                const start = parseISO(event.startTime);
                const end = parseISO(event.endTime);
                return start < addHours(hour, 1) && end > hour;
              })
              .map(event => (
                <WeekEventChip
                  key={event.id}
                  event={event}
                  hour={hour}
                  onClick={(e) => { e.stopPropagation(); onEventClick(event); }}
                />
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function EventChip({ event, onClick }: { event: Event; onClick: (e: React.MouseEvent) => void }) {
  const color = event.category?.color || '#6366F1';
  return (
    <div
      className="calendar-event cursor-pointer"
      style={{
        background: `${color}15`,
        color,
        borderLeftColor: color,
      }}
      onClick={onClick}
    >
      {event.title}
    </div>
  );
}

function WeekEventChip({ event, hour, onClick }: { event: Event; hour: Date; onClick: (e: React.MouseEvent) => void }) {
  const color = event.category?.color || '#6366F1';
  const start = parseISO(event.startTime);
  const end = parseISO(event.endTime);
  const hourStart = hour.getHours();

  const top = Math.max(0, (start.getHours() - hourStart) * 60 + start.getMinutes()) * (60 / 60);
  const height = Math.min(60, (end.getHours() - hourStart) * 60 + end.getMinutes() - ((start.getHours() - hourStart) * 60 + start.getMinutes()));

  return (
    <div
      className="week-event cursor-pointer"
      style={{
        top: `${top}px`,
        height: `${Math.max(20, height)}px`,
        background: `${color}15`,
        color,
        borderLeftColor: color,
      }}
      onClick={onClick}
    >
      <div className="font-medium truncate">{event.title}</div>
      <div className="text-xs opacity-75 truncate">{format(start, 'HH:mm')} - {format(end, 'HH:mm')}</div>
    </div>
  );
}

// Event Modal
type EventModalCategory = {
  id: string;
  name: string;
  children: Array<{ id: string; name: string }>;
};

type EventModalProps = {
  open: boolean;
  onClose: () => void;
  form: FormInstance;
  isEditing: boolean;
  categories: EventModalCategory[];
  userTimezone: string;
  onSubmit: (values: Record<string, unknown>) => void;
  submitting: boolean;
};

function EventModal({ open, onClose, form, isEditing, categories, userTimezone, onSubmit, submitting }: EventModalProps) {
  return (
    <Modal
      open={open}
      onCancel={onClose}
      title={isEditing ? 'Edit Event' : 'Create Event'}
      width={560}
      footer={null}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onSubmit} className="space-y-4 p-4">
        <Form.Item name="title" label="Title" rules={[{ required: true, message: 'Title is required' }]}>
          <Input placeholder="Event title" />
        </Form.Item>

        <Form.Item name="description" label="Description">
          <Input.TextArea placeholder="Description" rows={3} />
        </Form.Item>

        <Form.Item name="location" label="Location">
          <Input placeholder="Location (optional)" />
        </Form.Item>

        <Form.Item name="categoryId" label="Category">
          <Select
            placeholder="Select category"
            options={categories.flatMap(c => [
              { value: c.id, label: c.name, disabled: !!c.children.length },
              ...c.children.map(sc => ({ value: sc.id, label: `  └ ${sc.name}` })),
            ])}
            showSearch
            style={{ width: '100%' }}
          />
        </Form.Item>

        <div className="grid grid-cols-2 gap-4">
          <Form.Item name="startTime" label="Start" rules={[{ required: true }]}>
            <DatePicker
              format="YYYY-MM-DD HH:mm"
              showTime
              placeholder="Start time"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item name="endTime" label="End" rules={[{ required: true }]}>
            <DatePicker
              format="YYYY-MM-DD HH:mm"
              showTime
              placeholder="End time"
              style={{ width: '100%' }}
            />
          </Form.Item>
        </div>

        <Form.Item name="allDay" label="All day" valuePropName="checked">
          <Radio.Group>
            <Radio.Button value={false}>Timed</Radio.Button>
            <Radio.Button value={true}>All day</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item name="priority" label="Priority">
          <Select
            placeholder="Priority"
            options={[
              { value: 'NORMAL', label: 'Normal' },
              { value: 'HIGH', label: 'High' },
              { value: 'CRITICAL', label: 'Critical' },
            ]}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item name="status" label="Status">
          <Select
            placeholder="Status"
            options={[
              { value: 'SCHEDULED', label: 'Scheduled' },
              { value: 'COMPLETED', label: 'Completed' },
              { value: 'CANCELLED', label: 'Cancelled' },
            ]}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item name="preparationNotes" label="Preparation Notes">
          <Input.TextArea placeholder="Notes for preparation" rows={2} />
        </Form.Item>

        <RecurrenceEditor
          form={form}
          name="recurrence"
          label="Recurrence"
          required={false}
        />

        <Form.Item name="timezone" label="Timezone" className="hidden">
          <Input defaultValue={userTimezone} />
        </Form.Item>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="text" onClick={onClose}>
            Cancel
          </Button>
          <Button type="primary" htmlType="submit" loading={submitting}>
            {isEditing ? 'Save Changes' : 'Create Event'}
          </Button>
        </div>
      </Form>
    </Modal>
  );
}