import { format, parseISO, startOfDay, endOfDay, startOfWeek, endOfWeek, startOfMonth, endOfMonth, addDays, addWeeks, addMonths, subDays, subWeeks, subMonths, isSameDay, isSameMonth, isToday, isBefore, isAfter, differenceInMinutes, differenceInHours, differenceInDays } from 'date-fns';
import { fromZonedTime, toZonedTime, formatInTimeZone } from 'date-fns-tz';

export const TIMEZONE = 'UTC';

export function setTimezone(timezone: string) {
  // This would be called with user's timezone
}

export function toUTC(date: Date, timezone: string = TIMEZONE): Date {
  return fromZonedTime(date, timezone);
}

export function fromUTC(date: Date, timezone: string = TIMEZONE): Date {
  return toZonedTime(date, timezone);
}

export function formatInZone(date: Date, formatStr: string, timezone: string = TIMEZONE): string {
  return formatInTimeZone(date, timezone, formatStr);
}

export function formatDate(date: Date | string, formatStr: string = 'PPP', timezone: string = TIMEZONE): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatInZone(d, formatStr, timezone);
}

export function formatTime(date: Date | string, formatStr: string = 'HH:mm', timezone: string = TIMEZONE): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatInZone(d, formatStr, timezone);
}

export function formatDateTime(date: Date | string, formatStr: string = 'PPP HH:mm', timezone: string = TIMEZONE): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatInZone(d, formatStr, timezone);
}

export function formatRelativeTime(date: Date | string, timezone: string = TIMEZONE): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const diffMins = Math.round(diffMs / 60000);
  const diffHours = Math.round(diffMs / 3600000);
  const diffDays = Math.round(diffMs / 86400000);

  if (Math.abs(diffMins) < 1) return 'just now';
  if (Math.abs(diffMins) < 60) return `${diffMins > 0 ? 'in ' : ''}${Math.abs(diffMins)}m`;
  if (Math.abs(diffHours) < 24) return `${diffHours > 0 ? 'in ' : ''}${Math.abs(diffHours)}h`;
  if (Math.abs(diffDays) < 7) return `${diffDays > 0 ? 'in ' : ''}${Math.abs(diffDays)}d`;

  return formatDate(d, 'PPP', timezone);
}

export function getMonthStart(date: Date = new Date()): Date {
  return startOfMonth(date);
}

export function getMonthEnd(date: Date = new Date()): Date {
  return endOfMonth(date);
}

export function getWeekStart(date: Date = new Date(), weekStartsOn: 0 | 1 | 2 | 3 | 4 | 5 | 6 = 0): Date {
  return startOfWeek(date, { weekStartsOn });
}

export function getWeekEnd(date: Date = new Date(), weekStartsOn: 0 | 1 | 2 | 3 | 4 | 5 | 6 = 0): Date {
  return endOfWeek(date, { weekStartsOn });
}

export function getDayStart(date: Date = new Date()): Date {
  return startOfDay(date);
}

export function getDayEnd(date: Date = new Date()): Date {
  return endOfDay(date);
}

export function addMonthsSafe(date: Date, months: number): Date {
  return addMonths(date, months);
}

export function addWeeksSafe(date: Date, weeks: number): Date {
  return addWeeks(date, weeks);
}

export function addDaysSafe(date: Date, days: number): Date {
  return addDays(date, days);
}

export function subMonthsSafe(date: Date, months: number): Date {
  return subMonths(date, months);
}

export function subWeeksSafe(date: Date, weeks: number): Date {
  return subWeeks(date, weeks);
}

export function subDaysSafe(date: Date, days: number): Date {
  return subDays(date, days);
}

export function isSameDaySafe(date1: Date, date2: Date): boolean {
  return isSameDay(date1, date2);
}

export function isSameMonthSafe(date1: Date, date2: Date): boolean {
  return isSameMonth(date1, date2);
}

export function isTodaySafe(date: Date): boolean {
  return isToday(date);
}

export function isBeforeSafe(date1: Date, date2: Date): boolean {
  return isBefore(date1, date2);
}

export function isAfterSafe(date1: Date, date2: Date): boolean {
  return isAfter(date1, date2);
}

export function getMinutesUntil(date: Date): number {
  return Math.max(0, differenceInMinutes(date, new Date()));
}

export function getHoursUntil(date: Date): number {
  return Math.max(0, differenceInHours(date, new Date()));
}

export function getDaysUntil(date: Date): number {
  return Math.max(0, differenceInDays(date, new Date()));
}

export function generateTimeSlots(startHour: number = 0, endHour: number = 24, intervalMinutes: number = 60): Date[] {
  const slots: Date[] = [];
  const baseDate = new Date();
  baseDate.setHours(startHour, 0, 0, 0);

  for (let hour = startHour; hour < endHour; hour += intervalMinutes / 60) {
    const slot = new Date(baseDate);
    slot.setHours(hour);
    slots.push(slot);
  }

  return slots;
}

export function getCalendarWeeks(monthStart: Date, monthEnd: Date, weekStartsOn: 0 | 1 | 2 | 3 | 4 | 5 | 6 = 0): Date[][] {
  const weeks: Date[][] = [];
  let currentWeek = getWeekStart(monthStart, weekStartsOn);

  while (isBeforeSafe(currentWeek, monthEnd) || isSameDaySafe(currentWeek, monthEnd)) {
    const week: Date[] = [];
    for (let i = 0; i < 7; i++) {
      week.push(addDaysSafe(currentWeek, i));
    }
    weeks.push(week);
    currentWeek = addWeeksSafe(currentWeek, 1);
  }

  return weeks;
}

export function parseISODate(dateStr: string): Date {
  return parseISO(dateStr);
}

export function toISOString(date: Date): string {
  return date.toISOString();
}