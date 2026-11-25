import { Controller, ControllerProps, FieldPath, FieldValues, UseFormReturn, Control } from "react-hook-form";
import { Input, InputProps } from "antd";
import { ReactNode, useState, useEffect, ChangeEvent } from "react";

interface AppPasswordInputProps<T extends FieldValues> extends Omit<InputProps, "value" | "onChange" | "defaultValue" | "type" | "ref"> {
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
  /** Placeholder text */
  placeholder?: string;
  /** Auto-complete attribute */
  autoComplete?: string;
  /** Whether the input is required */
  required?: boolean;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Input ID */
  id?: string;
  /** Show/hide password visibility toggle */
  showVisibilityToggle?: boolean;
  /** Visibility toggle icon show text */
  visibilityToggleShowIcon?: ReactNode;
  /** Visibility toggle icon hide text */
  visibilityToggleHideIcon?: ReactNode;
}

export function AppPasswordInput<T extends FieldValues>({
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
  placeholder = "••••••••",
  autoComplete = "current-password",
  required = false,
  disabled = false,
  id,
  showVisibilityToggle = true,
  visibilityToggleShowIcon,
  visibilityToggleHideIcon,
  className,
  style,
  onBlur,
  onFocus,
  ...rest
}: AppPasswordInputProps<T>) {
  const [showPassword, setShowPassword] = useState(false);
  const [hasFocus, setHasFocus] = useState(false);

  // Auto-hide password when field loses focus
  useEffect(() => {
    if (!hasFocus && showPassword) {
      setShowPassword(false);
    }
  }, [hasFocus, showPassword]);

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

        const handleVisibilityToggle = () => {
          setShowPassword(!showPassword);
        };

        const handleBlur = () => {
          setHasFocus(false);
          field.onBlur();
          if (validateOnBlur) {
            control._subjects.state.next({ isSubmitted: true });
          }
        };

        const handleFocus = () => {
          setHasFocus(true);
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
            <Input.Password
              {...rest}
              className={className}
              style={style}
              disabled={disabled}
              placeholder={placeholder}
              autoComplete={autoComplete}
              id={id}
              prefix={prefix}
              suffix={
                <>
                  {suffix}
                  {showVisibilityToggle && (
                    <span
                      className="cursor-pointer text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)] transition-colors"
                      onClick={handleVisibilityToggle}
                      onMouseDown={(e) => e.preventDefault()} // Prevent focus loss
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          handleVisibilityToggle();
                        }
                      }}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      aria-pressed={showPassword}
                    >
                      {showPassword
                        ? visibilityToggleHideIcon || (
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                              <line x1="1" y1="1" x2="23" y2="23"></line>
                            </svg>
                          )
                        : visibilityToggleShowIcon || (
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                              <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                          )}
                    </span>
                  )}
                </>
              }
              type={showPassword ? "text" : "password"}
              value={(field.value || "") as string}
              status={hasError ? "error" : undefined}
              onBlur={handleBlur}
              onFocus={handleFocus}
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

// Confirm password input with built-in match validation
interface AppConfirmPasswordInputProps<T extends FieldValues> extends Omit<AppPasswordInputProps<T>, "rules"> {
  /** The field name to match against (e.g., "password") */
  matchField: FieldPath<T>;
  /** Custom error message when passwords don't match */
  matchErrorMessage?: string;
  /** Original password field control (optional - uses same control if not provided) */
  matchControl?: UseFormReturn<T>["control"];
}

export function AppConfirmPasswordInput<T extends FieldValues>({
  control,
  name,
  matchField,
  matchErrorMessage = "Passwords do not match",
  matchControl,
  label,
  error,
  helpText,
  prefix,
  suffix,
  validateOnBlur = true,
  validateOnChange = false,
  placeholder = "••••••••",
  autoComplete = "new-password",
  required = false,
  disabled = false,
  id,
  showVisibilityToggle = true,
  visibilityToggleShowIcon,
  visibilityToggleHideIcon,
  className,
  style,
  onBlur,
  onFocus,
  ...rest
}: AppConfirmPasswordInputProps<T>) {
  const [showPassword, setShowPassword] = useState(false);
  const [hasFocus, setHasFocus] = useState(false);

  // Use the same control by default
  const effectiveMatchControl: Control<T> = matchControl || control;

  useEffect(() => {
    if (!hasFocus && showPassword) {
      setShowPassword(false);
    }
  }, [hasFocus, showPassword]);

  return (
    <Controller<T>
      control={control}
      name={name}
      rules={{
        required: required ? "Please confirm your password" : undefined,
        validate: (value) => {
          // Use form watch to get the current value
          const matchValue = effectiveMatchControl._getWatch(matchField as string, effectiveMatchControl._formValues as any);
          if (value && matchValue && value !== matchValue) {
            return matchErrorMessage;
          }
          return true;
        },
      }}
      render={({ field, fieldState }) => {
        const hasError = error || fieldState.error;
        const errorMessage = hasError ? (typeof hasError === "string" ? hasError : hasError.message) : undefined;

        const handleVisibilityToggle = () => {
          setShowPassword(!showPassword);
        };

        const handleBlur = () => {
          setHasFocus(false);
          field.onBlur();
          if (validateOnBlur) {
            control._subjects.state.next({ isSubmitted: true });
          }
        };

        const handleFocus = () => {
          setHasFocus(true);
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
            <Input.Password
              {...rest}
              className={className}
              style={style}
              disabled={disabled}
              placeholder={placeholder}
              autoComplete={autoComplete}
              id={id}
              prefix={prefix}
              suffix={
                <>
                  {suffix}
                  {showVisibilityToggle && (
                    <span
                      className="cursor-pointer text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)] transition-colors"
                      onClick={handleVisibilityToggle}
                      onMouseDown={(e) => e.preventDefault()}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          handleVisibilityToggle();
                        }
                      }}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      aria-pressed={showPassword}
                    >
                      {showPassword
                        ? visibilityToggleHideIcon || (
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                              <line x1="1" y1="1" x2="23" y2="23"></line>
                            </svg>
                          )
                        : visibilityToggleShowIcon || (
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                              <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                          )}
                    </span>
                  )}
                </>
              }
              type={showPassword ? "text" : "password"}
              value={(field.value || "") as string}
              status={hasError ? "error" : undefined}
              onBlur={handleBlur}
              onFocus={handleFocus}
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