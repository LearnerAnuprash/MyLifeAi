import { useState, useMemo } from "react";
import { Form, Select, Input, Radio, Switch, DatePicker, Space, Divider, Collapse, Tooltip } from "antd";
import { ExclamationCircleOutlined, ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import clsx from "clsx";

// Using RotationOutlined instead of RepeatOutlined which doesn't exist
const RepeatOutlined = () => <ReloadOutlined />;

interface RecurrenceRule {
  freq: "DAILY" | "WEEKLY" | "MONTHLY" | "YEARLY";
  interval: number;
  byWeekday?: number[]; // 0=SU, 1=MO, ..., 6=SA
  byMonthDay?: number[];
  byMonth?: number[];
  count?: number;
  until?: Date;
}

interface RecurrenceEditorProps {
  form: any;
  name: string;
  label?: string;
  required?: boolean;
}

const WEEKDAYS = [
  { value: 0, label: "Sunday", short: "SU" },
  { value: 1, label: "Monday", short: "MO" },
  { value: 2, label: "Tuesday", short: "TU" },
  { value: 3, label: "Wednesday", short: "WE" },
  { value: 4, label: "Thursday", short: "TH" },
  { value: 5, label: "Friday", short: "FR" },
  { value: 6, label: "Saturday", short: "SA" },
];

const FREQUENCIES = [
  { value: "DAILY", label: "Daily" },
  { value: "WEEKLY", label: "Weekly" },
  { value: "MONTHLY", label: "Monthly" },
  { value: "YEARLY", label: "Yearly" },
];

const MONTHS = [
  { value: 1, label: "January" },
  { value: 2, label: "February" },
  { value: 3, label: "March" },
  { value: 4, label: "April" },
  { value: 5, label: "May" },
  { value: 6, label: "June" },
  { value: 7, label: "July" },
  { value: 8, label: "August" },
  { value: 9, label: "September" },
  { value: 10, label: "October" },
  { value: 11, label: "November" },
  { value: 12, label: "December" },
];

function rruleToString(rule: RecurrenceRule): string {
  const parts = [`FREQ=${rule.freq}`];

  if (rule.interval > 1) {
    parts.push(`INTERVAL=${rule.interval}`);
  }

  if (rule.byWeekday && rule.byWeekday.length > 0) {
    const dayNames = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"];
    parts.push(`BYDAY=${rule.byWeekday.map(d => dayNames[d]).join(",")}`);
  }

  if (rule.byMonthDay && rule.byMonthDay.length > 0) {
    parts.push(`BYMONTHDAY=${rule.byMonthDay.join(",")}`);
  }

  if (rule.byMonth && rule.byMonth.length > 0) {
    parts.push(`BYMONTH=${rule.byMonth.join(",")}`);
  }

  if (rule.count) {
    parts.push(`COUNT=${rule.count}`);
  }

  if (rule.until) {
    const untilStr = rule.until.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
    parts.push(`UNTIL=${untilStr}`);
  }

  return parts.join(";");
}

function parseRrule(rruleStr: string): Partial<RecurrenceRule> {
  const rule: Partial<RecurrenceRule> = {
    freq: "WEEKLY",
    interval: 1,
  };

  const parts = rruleStr.split(";");
  for (const part of parts) {
    const [key, value] = part.split("=");
    switch (key) {
      case "FREQ":
        rule.freq = value as RecurrenceRule["freq"];
        break;
      case "INTERVAL":
        rule.interval = parseInt(value, 10);
        break;
      case "BYDAY": {
        const dayNames = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"];
        rule.byWeekday = value.split(",").map(d => dayNames.indexOf(d)).filter(i => i >= 0);
        break;
      }
      case "BYMONTHDAY":
        rule.byMonthDay = value.split(",").map(v => parseInt(v, 10));
        break;
      case "BYMONTH":
        rule.byMonth = value.split(",").map(v => parseInt(v, 10));
        break;
      case "COUNT":
        rule.count = parseInt(value, 10);
        break;
      case "UNTIL":
        rule.until = new Date(value.replace(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z/, "$1-$2-$3T$4:$5:$6Z"));
        break;
    }
  }

  return rule;
}

export function RecurrenceEditor({ form, name, label = "Recurrence", required = false }: RecurrenceEditorProps) {
  const [isRecurring, setIsRecurring] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const rruleField = `${name}.rrule`;
  const recurrenceEndField = `${name}.recurrenceEnd`;
  const recurrenceEndTypeField = `${name}.recurrenceEndType`;

  const currentRrule = form.getFieldValue(rruleField);
  const currentEnd = form.getFieldValue(recurrenceEndField);
  const currentEndType = form.getFieldValue(recurrenceEndTypeField) || "never";

  const parsedRule = useMemo(() => {
    if (!currentRrule) return { freq: "WEEKLY" as const, interval: 1 };
    return parseRrule(currentRrule);
  }, [currentRrule]);

  const handleRruleChange = (newRule: Partial<RecurrenceRule>) => {
    const merged = { ...parsedRule, ...newRule };
    form.setFieldsValue({
      [rruleField]: rruleToString(merged as RecurrenceRule),
    });
  };

  const handleRecurringToggle = (value: boolean) => {
    setIsRecurring(value);
    setExpanded(value);
    if (!value) {
      form.setFieldsValue({
        [rruleField]: "",
        [recurrenceEndField]: "",
        [recurrenceEndTypeField]: "never",
      });
    } else {
      form.setFieldsValue({
        [rruleField]: rruleToString({ freq: "WEEKLY", interval: 1 }),
        [recurrenceEndTypeField]: "never",
      });
    }
  };

  if (!isRecurring) {
    return (
      <Form.Item name={name} label={label} className="space-y-3" noStyle>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Switch
            checked={isRecurring}
            onChange={handleRecurringToggle}
            checkedChildren="Recurring Event"
            unCheckedChildren="One-time Event"
            size="small"
          />
          {required && (
            <Tooltip title="This field is required">
              <ExclamationCircleOutlined className="text-error-500" />
            </Tooltip>
          )}
        </Space>
      </Form.Item>
    );
  }

  return (
    <Form.Item name={name} label={label} className="space-y-3" noStyle>
      <Collapse
        activeKey={expanded ? ["recurrence"] : []}
        onChange={(keys) => setExpanded(keys.length > 0)}
        accordion
        className="border border-[var(--color-border-primary)] rounded-lg overflow-hidden"
      >
        <Collapse.Panel key="recurrence" header={
          <Space>
            <RepeatOutlined />
            <span className="font-medium">Recurrence Rules</span>
            <Switch
              checked={isRecurring}
              onChange={handleRecurringToggle}
              size="small"
            />
            {required && <ExclamationCircleOutlined className="text-error-500" />}
          </Space>
        }>
          <div className="space-y-4 p-4">
            {/* Frequency */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                Frequency
              </label>
              <Select
                value={parsedRule.freq}
                onChange={(v) => handleRruleChange({ freq: v as any })}
                style={{ width: "100%" }}
                options={FREQUENCIES}
              />
            </div>

            {/* Interval */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                Every {parsedRule.interval || 1} {parsedRule.freq?.toLowerCase() || "week"}(s)
              </label>
              <Input
                type="number"
                value={parsedRule.interval || 1}
                min={1}
                max={99}
                onChange={(e) => handleRruleChange({ interval: parseInt(e.target.value, 10) || 1 })}
                style={{ width: "100%" }}
              />
            </div>

            {/* Frequency-specific options */}
            {(parsedRule.freq === "WEEKLY" || parsedRule.freq === "MONTHLY" || parsedRule.freq === "YEARLY") && (
              <Divider>Repeat on</Divider>
            )}

            {parsedRule.freq === "WEEKLY" && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                  Days of Week
                </label>
                <Space wrap size={[8, 8]}>
                  {WEEKDAYS.map(day => (
                    <label key={day.value} className={clsx(
                      "inline-flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors",
                      parsedRule.byWeekday?.includes(day.value)
                        ? "bg-[var(--color-primary-bg)] border-[var(--color-primary-border)] text-[var(--color-primary-text)]"
                        : "border-[var(--color-border-primary)] hover:bg-[var(--color-bg-hover)]"
                    )}>
                      <input
                        type="checkbox"
                        checked={parsedRule.byWeekday?.includes(day.value) || false}
                        onChange={(e) => {
                          const current = parsedRule.byWeekday || [];
                          const updated = e.target.checked
                            ? [...current, day.value]
                            : current.filter(d => d !== day.value);
                          handleRruleChange({ byWeekday: updated });
                        }}
                        className="hidden"
                      />
                      <span className="font-medium">{day.short}</span>
                      <span className="text-xs text-[var(--color-text-tertiary)]">{day.label}</span>
                    </label>
                  ))}
                </Space>
              </div>
            )}

            {parsedRule.freq === "MONTHLY" && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                  Day of Month
                </label>
                <Space wrap size={[8, 8]}>
                  {Array.from({ length: 31 }, (_, i) => i + 1).map(day => (
                    <label key={day} className={clsx(
                      "inline-flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors",
                      parsedRule.byMonthDay?.includes(day)
                        ? "bg-[var(--color-primary-bg)] border-[var(--color-primary-border)] text-[var(--color-primary-text)]"
                        : "border-[var(--color-border-primary)] hover:bg-[var(--color-bg-hover)]"
                    )}>
                      <input
                        type="checkbox"
                        checked={parsedRule.byMonthDay?.includes(day) || false}
                        onChange={(e) => {
                          const current = parsedRule.byMonthDay || [];
                          const updated = e.target.checked
                            ? [...current, day]
                            : current.filter(d => d !== day);
                          handleRruleChange({ byMonthDay: updated });
                        }}
                        className="hidden"
                      />
                      <span className="font-medium">{day}</span>
                    </label>
                  ))}
                </Space>
              </div>
            )}

            {parsedRule.freq === "YEARLY" && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                  Months
                </label>
                <Space wrap size={[8, 8]}>
                  {MONTHS.map(month => (
                    <label key={month.value} className={clsx(
                      "inline-flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors",
                      parsedRule.byMonth?.includes(month.value)
                        ? "bg-[var(--color-primary-bg)] border-[var(--color-primary-border)] text-[var(--color-primary-text)]"
                        : "border-[var(--color-border-primary)] hover:bg-[var(--color-bg-hover)]"
                    )}>
                      <input
                        type="checkbox"
                        checked={parsedRule.byMonth?.includes(month.value) || false}
                        onChange={(e) => {
                          const current = parsedRule.byMonth || [];
                          const updated = e.target.checked
                            ? [...current, month.value]
                            : current.filter(d => d !== month.value);
                          handleRruleChange({ byMonth: updated });
                        }}
                        className="hidden"
                      />
                      <span className="text-sm">{month.label}</span>
                    </label>
                  ))}
                </Space>
              </div>
            )}

            <Divider>Ends</Divider>

            <Space direction="vertical" style={{ width: "100%" }} size="middle">
              <Radio.Group
                value={currentEndType}
                onChange={(e) => form.setFieldValue(recurrenceEndTypeField, e.target.value)}
              >
                <Radio value="never">Never</Radio>
                <Radio value="count">After</Radio>
                <Radio value="until">On Date</Radio>
              </Radio.Group>

              {currentEndType === "count" && (
                <Form.Item name={recurrenceEndField} rules={[{ required: true, message: "Enter occurrence count" }]} noStyle>
                  <Input
                    type="number"
                    min={1}
                    max={999}
                    value={currentEnd ? parseInt(currentEnd, 10) : 1}
                    onChange={(e) => form.setFieldValue(recurrenceEndField, e.target.value || "1")}
                    style={{ width: "100%" }}
                    addonAfter="occurrences"
                  />
                </Form.Item>
              )}

              {currentEndType === "until" && (
                <Form.Item name={recurrenceEndField} rules={[{ required: true, message: "Select end date" }]} noStyle>
                  <DatePicker
                    format="YYYY-MM-DD"
                    value={currentEnd ? dayjs(currentEnd) : null}
                    onChange={(date) => form.setFieldValue(recurrenceEndField, date ? date.toISOString() : "")}
                    style={{ width: "100%" }}
                    placeholder="Select end date"
                  />
                </Form.Item>
              )}
            </Space>

            {/* Preview */}
            {parsedRule.freq && (
              <Divider>Preview</Divider>
            )}

            <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-3 text-sm">
              <span className="font-medium text-[var(--color-text-primary)]">
                {getRecurrenceDescription(parsedRule, currentEndType, currentEnd)}
              </span>
            </div>
          </div>
        </Collapse.Panel>
      </Collapse>
    </Form.Item>
  );
}

function getRecurrenceDescription(
  rule: Partial<RecurrenceRule>,
  endType: string,
  endValue: string
): string {
  const freqLabels: Record<string, string> = {
    DAILY: "day",
    WEEKLY: "week",
    MONTHLY: "month",
    YEARLY: "year",
  };

  const interval = rule.interval || 1;
  const freq = rule.freq || "WEEKLY";
  const unit = freqLabels[freq] || "week";

  let desc = `Every ${interval === 1 ? "" : `${interval} `}${interval === 1 ? unit : unit + "s"}`;

  if (freq === "WEEKLY" && rule.byWeekday && rule.byWeekday.length > 0) {
    const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    desc += ` on ${rule.byWeekday.map(d => dayNames[d]).join(", ")}`;
  }

  if (freq === "MONTHLY" && rule.byMonthDay && rule.byMonthDay.length > 0) {
    desc += ` on day ${rule.byMonthDay.join(", ")} of the month`;
  }

  if (freq === "YEARLY" && rule.byMonth && rule.byMonth.length > 0) {
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    desc += ` in ${rule.byMonth.map(m => monthNames[m - 1]).join(", ")}`;
  }

  if (endType === "count" && endValue) {
    desc += `, ${endValue} time${endValue !== "1" ? "s" : ""}`;
  } else if (endType === "until" && endValue) {
    const untilDate = new Date(endValue);
    desc += `, until ${untilDate.toLocaleDateString()}`;
  } else if (endType === "never") {
    desc += ", forever";
  }

  return desc;
}

export { parseRrule, rruleToString };