import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Button,
  Switch,
  Card,
  Divider,
  Tabs,
  message,
} from "antd";
import {
  UserOutlined,
  BgColorsOutlined,
  CalendarOutlined,
  BellOutlined,
  RobotOutlined,
  GlobalOutlined,
  TagOutlined,
  SunOutlined,
  MoonOutlined,
  LaptopOutlined,
} from "@ant-design/icons";
import { CategoryManagement } from "@/components/categories";
import { useTheme } from "@/store/themeStore";
import { useAuthStore } from "@/store/authStore";
import { graphqlRequestWithAuth } from "@/utils/graphqlClient";
import clsx from "clsx";
import { AppInput, AppSelect } from "@/components/ui";
import { UPDATE_SETTINGS_MUTATION } from "@/graphql/operations";

const settingsSchema = z.object({
  // Profile
  fullName: z.string().min(2).optional(),
  timezone: z.string().optional(),
  locale: z.string().optional(),
  // Appearance
  theme: z.enum(["light", "dark", "system"]).optional(),
  calendarDefaultView: z
    .enum(["month", "week", "day", "year", "upcoming", "past"])
    .optional(),
  weekStartDay: z.number().min(0).max(6).optional(),
  dateFormat: z.string().optional(),
  timeFormat: z.enum(["12h", "24h"]).optional(),
  // Notifications
  defaultReminderMinutes: z.array(z.number()).optional(),
  notificationEmail: z.boolean().optional(),
  notificationPush: z.boolean().optional(),
  // AI
  aiProvider: z.string().optional(),
  aiModel: z.string().optional(),
  // Language
  language: z.string().optional(),
});

type SettingsForm = z.infer<typeof settingsSchema>;

const TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Rome",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Singapore",
  "Asia/Dubai",
  "Australia/Sydney",
  "Pacific/Auckland",
];

const LOCALES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "it", label: "Italian" },
  { value: "pt", label: "Portuguese" },
  { value: "ja", label: "Japanese" },
  { value: "zh", label: "Chinese" },
];

const AI_PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
];

const AI_MODELS = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  anthropic: [
    "claude-3-5-sonnet",
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
  ],
};

const CALENDAR_VIEWS = [
  { value: "month", label: "Month" },
  { value: "week", label: "Week" },
  { value: "day", label: "Day" },
  { value: "year", label: "Year" },
  { value: "upcoming", label: "Upcoming" },
  { value: "past", label: "Past" },
];

const WEEK_START_DAYS = [
  { value: 0, label: "Sunday" },
  { value: 1, label: "Monday" },
  { value: 6, label: "Saturday" },
];

const DATE_FORMATS = [
  { value: "YYYY-MM-DD", label: "2024-01-15" },
  { value: "MM/DD/YYYY", label: "01/15/2024" },
  { value: "DD/MM/YYYY", label: "15/01/2024" },
  { value: "MMMM D, YYYY", label: "January 15, 2024" },
];

const TIME_FORMATS = [
  { value: "24h", label: "24-hour (14:30)" },
  { value: "12h", label: "12-hour (2:30 PM)" },
];

const REMINDER_OPTIONS = [
  { value: 5, label: "5 minutes" },
  { value: 15, label: "15 minutes" },
  { value: 30, label: "30 minutes" },
  { value: 60, label: "1 hour" },
  { value: 120, label: "2 hours" },
  { value: 360, label: "6 hours" },
  { value: 720, label: "12 hours" },
  { value: 1440, label: "1 day" },
  { value: 2880, label: "2 days" },
  { value: 10080, label: "1 week" },
];

export function SettingsPage() {
  const { user } = useAuthStore();
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [activeTab, setActiveTab] = useState("profile");
  const [isSaving, setIsSaving] = useState(false);

  const form = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      fullName: user?.fullName || "",
      timezone: user?.timezone || "UTC",
      locale: user?.locale || "en",
      theme: (user?.settings?.theme ?? "SYSTEM").toLowerCase() as SettingsForm["theme"],
      calendarDefaultView: (user?.settings?.calendarDefaultView ?? "MONTH").toLowerCase() as SettingsForm["calendarDefaultView"],
      weekStartDay: user?.settings?.weekStartDay || 0,
      dateFormat: user?.settings?.dateFormat || "YYYY-MM-DD",
      timeFormat: user?.settings?.timeFormat === "12h" ? "12h" : "24h",
      defaultReminderMinutes: user?.settings?.defaultReminderMinutes || [
        1440, 60, 15,
      ],
      notificationEmail: user?.settings?.notificationEmail || false,
      notificationPush: user?.settings?.notificationPush || false,
      aiProvider: user?.settings?.aiProvider || "openai",
      aiModel: user?.settings?.aiModel || "gpt-4o",
      language: user?.settings?.language || "en",
    },
    mode: "onBlur",
  });

  const handleThemeChange = (newTheme: "light" | "dark" | "system") => {
    form.setValue("theme", newTheme);
    setTheme(newTheme);
  };

  const onFinish = async (values: SettingsForm) => {
    setIsSaving(true);
    try {
      const input = {
        ...values,
        theme: values.theme?.toUpperCase(),
        calendarDefaultView: values.calendarDefaultView?.toUpperCase(),
      };
      const response = await graphqlRequestWithAuth<{ updateSettings: unknown }>(
        UPDATE_SETTINGS_MUTATION,
        { input },
      );

      if (response.data?.updateSettings) {
        message.success("Settings saved successfully");
      }
    } catch (error) {
      message.error(
        error instanceof Error ? error.message : "Failed to save settings",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { key: "profile", label: "Profile", icon: <UserOutlined /> },
    { key: "appearance", label: "Appearance", icon: <BgColorsOutlined /> },
    { key: "calendar", label: "Calendar", icon: <CalendarOutlined /> },
    { key: "notifications", label: "Notifications", icon: <BellOutlined /> },
    { key: "categories", label: "Categories", icon: <TagOutlined /> },
    { key: "ai", label: "AI Settings", icon: <RobotOutlined /> },
    { key: "language", label: "Language", icon: <GlobalOutlined /> },
  ];

  return (
    <div className="max-w-3xl mx-auto animate-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
          Settings
        </h1>
        <p className="text-[var(--color-text-secondary)]">
          Manage your preferences and account settings
        </p>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabs}
        className="mb-6"
      />

      <form onSubmit={form.handleSubmit(onFinish)} className="space-y-6">
        {/* Profile Tab */}
        <Card
          style={{ borderRadius: 12 }}
          className={activeTab === "profile" ? "" : "hidden"}
        >
          <div className="p-6 space-y-6">
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Profile Information
            </h3>

            <AppInput<SettingsForm>
              control={form.control}
              name="fullName"
              label="Full Name"
              placeholder="Your name"
              prefix={<UserOutlined className="text-[var(--color-text-tertiary)]" />}
              className="h-11"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AppSelect<SettingsForm>
                control={form.control}
                name="timezone"
                label="Timezone"
                placeholder="Select timezone"
                options={TIMEZONES.map((tz) => ({ value: tz, label: tz }))}
                showSearch
              />

              <AppSelect<SettingsForm>
                control={form.control}
                name="locale"
                label="Locale"
                placeholder="Select locale"
                options={LOCALES}
              />
            </div>

            <Divider>Email: {user?.email}</Divider>

            <Button type="primary" htmlType="submit" loading={isSaving} className="w-full">
              Save Profile
            </Button>
          </div>
        </Card>

        {/* Appearance Tab */}
        <Card
          style={{ borderRadius: 12 }}
          className={activeTab === "appearance" ? "" : "hidden"}
        >
          <div className="p-6 space-y-6">
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Appearance
            </h3>

            <div className="space-y-3">
              <label
                className={clsx(
                  "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
                  resolvedTheme === "light"
                    ? "bg-[var(--color-primary-bg)] border border-[var(--color-primary-border)]"
                    : "hover:bg-[var(--color-bg-hover)]",
                )}
              >
                <input
                  type="radio"
                  onChange={() => handleThemeChange("light")}
                  checked={resolvedTheme === "light"}
                  className="hidden"
                />
                <SunOutlined className="text-xl" />
                <div>
                  <p className="font-medium">Light</p>
                  <p className="text-sm text-[var(--color-text-tertiary)]">
                    Always use light mode
                  </p>
                </div>
              </label>

              <label
                className={clsx(
                  "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
                  resolvedTheme === "dark"
                    ? "bg-[var(--color-primary-bg)] border border-[var(--color-primary-border)]"
                    : "hover:bg-[var(--color-bg-hover)]",
                )}
              >
                <input
                  type="radio"
                  onChange={() => handleThemeChange("dark")}
                  checked={resolvedTheme === "dark"}
                  className="hidden"
                />
                <MoonOutlined className="text-xl" />
                <div>
                  <p className="font-medium">Dark</p>
                  <p className="text-sm text-[var(--color-text-tertiary)]">
                    Always use dark mode
                  </p>
                </div>
              </label>

              <label
                className={clsx(
                  "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
                  theme === "system" &&
                    resolvedTheme !== "dark" &&
                    resolvedTheme !== "light"
                    ? "bg-[var(--color-primary-bg)] border border-[var(--color-primary-border)]"
                    : "hover:bg-[var(--color-bg-hover)]",
                )}
              >
                <input
                  type="radio"
                  onChange={() => handleThemeChange("system")}
                  checked={theme === "system"}
                  className="hidden"
                />
                <LaptopOutlined className="text-xl" />
                <div>
                  <p className="font-medium">System</p>
                  <p className="text-sm text-[var(--color-text-tertiary)]">
                    Match system setting
                  </p>
                </div>
              </label>
            </div>

            <Button type="primary" htmlType="submit" loading={isSaving} className="w-full">
              Save Appearance
            </Button>
          </div>
        </Card>

        {/* Calendar Tab */}
        <Card
          style={{ borderRadius: 12 }}
          className={activeTab === "calendar" ? "" : "hidden"}
        >
          <div className="p-6 space-y-6">
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Calendar Preferences
            </h3>

            <AppSelect<SettingsForm>
              control={form.control}
              name="calendarDefaultView"
              label="Default View"
              placeholder="Select default view"
              options={CALENDAR_VIEWS}
            />

            <AppSelect<SettingsForm>
              control={form.control}
              name="weekStartDay"
              label="Week Starts On"
              placeholder="Select start day"
              options={WEEK_START_DAYS}
            />

            <AppSelect<SettingsForm>
              control={form.control}
              name="dateFormat"
              label="Date Format"
              placeholder="Select date format"
              options={DATE_FORMATS}
            />

            <AppSelect<SettingsForm>
              control={form.control}
              name="timeFormat"
              label="Time Format"
              placeholder="Select time format"
              options={TIME_FORMATS}
            />

            <Button type="primary" htmlType="submit" loading={isSaving} className="w-full">
              Save Calendar
            </Button>
          </div>
        </Card>

        {/* Notifications Tab */}
        <Card
          style={{ borderRadius: 12 }}
          className={activeTab === "notifications" ? "" : "hidden"}
        >
          <div className="p-6 space-y-6">
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Default Reminders
            </h3>
            <p className="text-[var(--color-text-secondary)]">
              Set default reminder times for new events (in minutes before
              event)
            </p>

            <AppSelect<SettingsForm>
              control={form.control}
              name="defaultReminderMinutes"
              label="Reminder Times"
              placeholder="Select reminder times"
              options={REMINDER_OPTIONS}
              mode="multiple"
              maxTagCount={3}
              maxTagPlaceholder="selected"
            />

            <Divider>Notification Channels</Divider>

            <div className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-[var(--color-text-primary)]">Email Notifications</span>
                <Switch
                  checked={form.watch("notificationEmail")}
                  onChange={(checked) => form.setValue("notificationEmail", checked)}
                />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-[var(--color-text-primary)]">Push Notifications</span>
                <Switch
                  checked={form.watch("notificationPush")}
                  onChange={(checked) => form.setValue("notificationPush", checked)}
                />
              </label>
            </div>

            <Button type="primary" htmlType="submit" loading={isSaving} className="w-full">
              Save Notifications
            </Button>
          </div>
        </Card>

        {/* Categories Tab */}
        <Card
          style={{ borderRadius: 12 }}
          className={activeTab === "categories" ? "" : "hidden"}
        >
          <CategoryManagement />
        </Card>

        {/* AI Tab */}
        <Card
          style={{ borderRadius: 12 }}
          className={activeTab === "ai" ? "" : "hidden"}
        >
          <div className="p-6 space-y-6">
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              AI Planner Settings
            </h3>

            <AppSelect<SettingsForm>
              control={form.control}
              name="aiProvider"
              label="AI Provider"
              placeholder="Select AI provider"
              options={AI_PROVIDERS}
            />

            <AppSelect<SettingsForm>
              control={form.control}
              name="aiModel"
              label="Model"
              placeholder="Select model"
              options={
                AI_MODELS[(form.watch("aiProvider") || "openai") as keyof typeof AI_MODELS]?.map((m) => ({
                  value: m,
                  label: m,
                })) || []
              }
            />

            <Button type="primary" htmlType="submit" loading={isSaving} className="w-full">
              Save AI Settings
            </Button>
          </div>
        </Card>

        {/* Language Tab */}
        <Card
          style={{ borderRadius: 12 }}
          className={activeTab === "language" ? "" : "hidden"}
        >
          <div className="p-6 space-y-6">
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Language & Region
            </h3>

            <AppSelect<SettingsForm>
              control={form.control}
              name="language"
              label="Language"
              placeholder="Select language"
              options={LOCALES}
            />

            <Button type="primary" htmlType="submit" loading={isSaving} className="w-full">
              Save Language
            </Button>
          </div>
        </Card>
      </form>
    </div>
  );
}
