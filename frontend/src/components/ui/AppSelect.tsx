import { Controller, ControllerProps, FieldPath, FieldValues, UseFormReturn, PathValue } from "react-hook-form";
import { Select, SelectProps } from "antd";
import { ReactNode } from "react";

interface SelectOption {
  value: string | number;
  label: ReactNode;
}

interface AppSelectProps<T extends FieldValues> extends Omit<SelectProps, "value" | "onChange" | "defaultValue" | "options" | "ref"> {
  /** The form control from react-hook-form */
  control: UseFormReturn<T>["control"];
  /** The field name for the form */
  name: FieldPath<T>;
  /** Optional label for the select */
  label?: string;
  /** Optional error message (will use form error if not provided) */
  error?: string;
  /** Optional help text */
  helpText?: string;
  /** Options for the select */
  options: SelectOption[];
  /** Rules for Controller (validation) */
  rules?: ControllerProps<T>["rules"];
  /** Whether to show validation error immediately on blur */
  validateOnBlur?: boolean;
  /** Whether to show validation error on change */
  validateOnChange?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Whether the select is required */
  required?: boolean;
  /** Whether the select is disabled */
  disabled?: boolean;
  /** Whether to show search */
  showSearch?: boolean;
  /** Select mode */
  mode?: SelectProps["mode"];
  /** Max tag count for multiple mode */
  maxTagCount?: number;
  /** Max tag placeholder for multiple mode */
  maxTagPlaceholder?: ReactNode;
  /** Input ID */
  id?: string;
}

export function AppSelect<T extends FieldValues>({
  control,
  name,
  label,
  error,
  helpText,
  options,
  rules,
  validateOnBlur = true,
  validateOnChange = false,
  placeholder = "Select an option",
  required = false,
  disabled = false,
  showSearch = false,
  mode,
  maxTagCount,
  maxTagPlaceholder,
  id,
  className,
  style,
  onBlur,
  onFocus,
  ...rest
}: AppSelectProps<T>) {
  const defaultValue = (mode === "multiple" ? [] : undefined) as PathValue<T, FieldPath<T>> | undefined;

  return (
    <Controller<T>
      control={control}
      name={name}
      rules={{
        ...rules,
        required: rules?.required || required ? "Please select an option" : undefined,
      }}
      defaultValue={defaultValue}
      render={({ field, fieldState }) => {
        const hasError = error || fieldState.error;
        const errorMessage = hasError ? (typeof hasError === "string" ? hasError : hasError.message) : undefined;

        const handleBlur = () => {
          field.onBlur();
          if (validateOnBlur) {
            control._subjects.state.next({ isSubmitted: true });
          }
        };

        const handleChange = (value: SelectProps["value"]) => {
          field.onChange(value as any);
          if (validateOnChange) {
            control._subjects.state.next({ isSubmitted: true });
          }
        };

        return (
          <div className="space-y-1.5">
            {label && (
              <label className="block text-sm font-medium text-[var(--color-text-secondary)]">
                {label}
                {required && <span className="text-error-500 ml-1" aria-hidden="true">*</span>}
              </label>
            )}
            <Select
              {...rest}
              className={className}
              style={style}
              disabled={disabled}
              placeholder={placeholder}
              options={options}
              showSearch={showSearch}
              mode={mode}
              maxTagCount={maxTagCount}
              maxTagPlaceholder={maxTagPlaceholder}
              id={id}
              value={field.value}
              status={hasError ? "error" : undefined}
              onBlur={handleBlur}
              onChange={handleChange}
            />
            {errorMessage && (
              <p className="text-sm text-error-500" role="alert">
                {errorMessage}
              </p>
            )}
            {helpText && !errorMessage && (
              <p className="text-sm text-[var(--color-text-tertiary)]">
                {helpText}
              </p>
            )}
          </div>
        );
      }}
    />
  );
}