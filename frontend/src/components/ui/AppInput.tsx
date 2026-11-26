import { Controller, ControllerProps, FieldPath, FieldValues, UseFormReturn } from "react-hook-form";
import { Input, InputProps } from "antd";
import { ReactNode, ChangeEvent } from "react";

interface AppInputProps<T extends FieldValues> extends Omit<InputProps, "value" | "onChange" | "defaultValue" | "ref"> {
  /** The form control from react-hook-form */
  control: UseFormReturn<T>["control"];
  /** The field name for the form */
  name: FieldPath<T>;
  /** Optional label for the input */
  label?: string;
  /** Optional error message (will use form error if not provided) */
  error?: string;
  /** Optional help text */
  helpText?: string;
  /** Optional prefix icon/node */
  prefix?: ReactNode;
  /** Optional suffix icon/node */
  suffix?: ReactNode;
  /** Rules for Controller (validation) */
  rules?: ControllerProps<T>["rules"];
  /** Whether to show validation error immediately on blur */
  validateOnBlur?: boolean;
  /** Whether to show validation error on change */
  validateOnChange?: boolean;
}

export function AppInput<T extends FieldValues>({
  control,
  name,
  label,
  error,
  helpText,
  prefix,
  suffix,
  rules,
  validateOnBlur = true,
  validateOnChange = false,
  className,
  style,
  disabled,
  required,
  placeholder,
  type = "text",
  autoComplete,
  id,
  ...rest
}: AppInputProps<T>) {
  return (
    <Controller<T>
      control={control}
      name={name}
      rules={{
        ...rules,
        required: rules?.required || required ? "This field is required" : undefined,
      }}
      render={({ field, fieldState }) => {
        const hasError = error || fieldState.error;
        const errorMessage = hasError ? (typeof hasError === "string" ? hasError : hasError.message) : undefined;

        const handleBlur = () => {
          field.onBlur();
          if (validateOnBlur) {
            control._subjects.state.next({ isSubmitted: true });
          }
        };

        const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
          field.onChange(event.target.value);
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
            <Input
              {...rest}
              className={className}
              style={style}
              disabled={disabled}
              placeholder={placeholder}
              type={type}
              autoComplete={autoComplete}
              id={id}
              prefix={prefix}
              suffix={suffix}
              value={(field.value || "") as string}
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

// TextArea props - only include props that are valid for TextArea
interface TextAreaProps {
  rows?: number;
  autoSize?: { minRows: number; maxRows: number } | boolean;
  className?: string;
  style?: React.CSSProperties;
  disabled?: boolean;
  placeholder?: string;
  autoComplete?: string;
  id?: string;
  onBlur?: React.FocusEventHandler<HTMLTextAreaElement>;
  onFocus?: React.FocusEventHandler<HTMLTextAreaElement>;
  onChange?: React.ChangeEventHandler<HTMLTextAreaElement>;
}

export interface AppTextAreaProps<T extends FieldValues> extends TextAreaProps {
  control: UseFormReturn<T>["control"];
  name: FieldPath<T>;
  label?: string;
  error?: string;
  helpText?: string;
  rules?: ControllerProps<T>["rules"];
  validateOnBlur?: boolean;
  validateOnChange?: boolean;
  required?: boolean;
}

export function AppTextArea<T extends FieldValues>({
  control,
  name,
  label,
  error,
  helpText,
  rules,
  validateOnBlur = true,
  validateOnChange = false,
  rows = 3,
  autoSize,
  className,
  style,
  disabled,
  required,
  placeholder,
  autoComplete,
  id,
  ...rest
}: AppTextAreaProps<T>) {
  return (
    <Controller<T>
      control={control}
      name={name}
      rules={{
        ...rules,
        required: rules?.required || required ? "This field is required" : undefined,
      }}
      render={({ field, fieldState }) => {
        const hasError = error || fieldState.error;
        const errorMessage = hasError ? (typeof hasError === "string" ? hasError : hasError.message) : undefined;

        const handleBlur = () => {
          field.onBlur();
          if (validateOnBlur) {
            control._subjects.state.next({ isSubmitted: true });
          }
        };

        const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
          field.onChange(event.target.value);
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
            <Input.TextArea
              {...rest}
              className={className}
              style={style}
              disabled={disabled}
              placeholder={placeholder}
              rows={rows}
              autoSize={autoSize}
              autoComplete={autoComplete}
              id={id}
              value={(field.value || "") as string}
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