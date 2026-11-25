import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Card, Alert, Tabs, message } from "antd";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { AppInput, AppPasswordInput, AppConfirmPasswordInput } from "@/components/ui";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

const registerSchema = z
  .object({
    fullName: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type LoginForm = z.infer<typeof loginSchema>;
type RegisterForm = z.infer<typeof registerSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loginForm = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
    mode: "onBlur",
  });

  const registerForm = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
    mode: "onBlur",
  });

  const handleLogin = async (values: LoginForm) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(
        import.meta.env.VITE_API_URL || "http://localhost:8000/graphql",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: `
            mutation Login($input: LoginInput!) {
              login(input: $input) {
                token
                user {
                  id
                  email
                  fullName
                  avatarUrl
                  timezone
                  locale
                  isActive
                  isVerified
                  createdAt
                  updatedAt
                  settings {
                    theme
                    calendarDefaultView
                    weekStartDay
                    defaultReminderMinutes
                    notificationEmail
                    notificationPush
                    aiProvider
                    aiModel
                    language
                    dateFormat
                    timeFormat
                  }
                }
              }
            }
          `,
            variables: { input: values },
          }),
        },
      );

      const result = await response.json();

      if (result.errors) {
        throw new Error(result.errors[0].message);
      }

      setAuth(result.data.login);
      message.success("Welcome back!");
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (values: RegisterForm) => {
    setError(null);
    setIsLoading(true);

    try {
      const { confirmPassword, ...input } = values;
      const response = await fetch(
        import.meta.env.VITE_API_URL || "http://localhost:8000/graphql",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: `
            mutation Register($input: RegisterInput!) {
              register(input: $input) {
                token
                user {
                  id
                  email
                  fullName
                  avatarUrl
                  timezone
                  locale
                  isActive
                  isVerified
                  createdAt
                  updatedAt
                  settings {
                    theme
                    calendarDefaultView
                    weekStartDay
                    defaultReminderMinutes
                    notificationEmail
                    notificationPush
                    aiProvider
                    aiModel
                    language
                    dateFormat
                    timeFormat
                  }
                }
              }
            }
          `,
            variables: { input },
          }),
        },
      );

      const result = await response.json();

      if (result.errors) {
        throw new Error(result.errors[0].message);
      }

      setAuth(result.data.register);
      message.success("Account created successfully!");
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-primary)] px-4">
      <Card
        className="w-full max-w-md animate-in"
        style={{ borderRadius: 16, boxShadow: "var(--shadow-xl)" }}
      >
        <div className="p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-500 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              My Life AI
            </h1>
            <p className="text-[var(--color-text-secondary)] mt-1">
              Intelligent life management
            </p>
          </div>

          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as "login" | "register")}
            className="mb-6"
            items={[
              { key: "login", label: "Sign In" },
              { key: "register", label: "Sign Up" },
            ]}
          />

          {error && (
            <Alert
              type="error"
              message="Error"
              description={error}
              className="mb-6"
              style={{ borderRadius: 8 }}
            />
          )}

          {activeTab === "login" ? (
            <form
              onSubmit={loginForm.handleSubmit(handleLogin)}
              className="space-y-4"
            >
              <AppInput<LoginForm>
                control={loginForm.control}
                name="email"
                label="Email"
                type="email"
                placeholder="you@example.com"
                required
                autoComplete="email"
                prefix={<span className="text-[var(--color-text-tertiary)]">✉️</span>}
                className="h-11"
              />

              <AppPasswordInput<LoginForm>
                control={loginForm.control}
                name="password"
                label="Password"
                placeholder="••••••••"
                required
                autoComplete="current-password"
                prefix={<span className="text-[var(--color-text-tertiary)]">🔒</span>}
                className="h-11"
              />

              <Button
                type="primary"
                htmlType="submit"
                className="w-full h-11 text-lg"
                loading={isLoading}
                style={{ borderRadius: 8 }}
              >
                Sign In
              </Button>
            </form>
          ) : (
            <form
              onSubmit={registerForm.handleSubmit(handleRegister)}
              className="space-y-4"
            >
              <AppInput<RegisterForm>
                control={registerForm.control}
                name="fullName"
                label="Full Name"
                placeholder="John Doe"
                required
                autoComplete="name"
                prefix={<span className="text-[var(--color-text-tertiary)]">👤</span>}
                className="h-11"
              />

              <AppInput<RegisterForm>
                control={registerForm.control}
                name="email"
                label="Email"
                type="email"
                placeholder="you@example.com"
                required
                autoComplete="email"
                prefix={<span className="text-[var(--color-text-tertiary)]">✉️</span>}
                className="h-11"
              />

              <AppPasswordInput<RegisterForm>
                control={registerForm.control}
                name="password"
                label="Password"
                placeholder="••••••••"
                required
                autoComplete="new-password"
                prefix={<span className="text-[var(--color-text-tertiary)]">🔒</span>}
                className="h-11"
                helpText="Must be at least 8 characters"
              />

              <AppConfirmPasswordInput<RegisterForm>
                control={registerForm.control}
                name="confirmPassword"
                matchField="password"
                label="Confirm Password"
                placeholder="••••••••"
                required
                autoComplete="new-password"
                prefix={<span className="text-[var(--color-text-tertiary)]">🔒</span>}
                className="h-11"
              />

              <Button
                type="primary"
                htmlType="submit"
                className="w-full h-11 text-lg"
                loading={isLoading}
                style={{ borderRadius: 8 }}
              >
                Create Account
              </Button>
            </form>
          )}

          <p className="text-center text-sm text-[var(--color-text-secondary)] mt-6">
            {activeTab === "login"
              ? "Don't have an account? "
              : "Already have an account? "}
            <span
              className="text-primary-500 font-medium cursor-pointer hover:underline"
              onClick={() =>
                setActiveTab(activeTab === "login" ? "register" : "login")
              }
            >
              {activeTab === "login" ? "Sign up" : "Sign in"}
            </span>
          </p>
        </div>
      </Card>
    </div>
  );
}