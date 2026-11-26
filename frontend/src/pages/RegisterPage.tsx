import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, Card, Alert, Tabs, message } from 'antd';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { graphqlRequest } from '@/utils/graphqlClient';
import type { AuthPayload } from '@/types/graphql';
import { REGISTER_MUTATION } from '@/graphql/operations';
import { AppInput, AppPasswordInput, AppConfirmPasswordInput } from '@/components/ui';

const registerSchema = z.object({
  fullName: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine(data => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const registerForm = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { fullName: '', email: '', password: '', confirmPassword: '' },
    mode: 'onBlur',
  });

  const handleRegister = async (values: RegisterForm) => {
    setError(null);
    setIsLoading(true);

    try {
      const { confirmPassword: _confirmPassword, ...input } = values;
      const response = await graphqlRequest<{ register: AuthPayload }>(
        REGISTER_MUTATION,
        { input },
      );

      if (response.errors?.length) {
        throw new Error(response.errors[0].message);
      }

      if (!response.data?.register) {
        throw new Error("Registration failed");
      }

      setAuth(response.data.register);
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
      <Card className="w-full max-w-md animate-in" style={{ borderRadius: 16, boxShadow: 'var(--shadow-xl)' }}>
        <div className="p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-500 flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">My Life AI</h1>
            <p className="text-[var(--color-text-secondary)] mt-1">Create your account</p>
          </div>

          <Tabs
            activeKey="register"
            className="mb-6"
            items={[
              { key: 'login', label: 'Sign In' },
              { key: 'register', label: 'Sign Up' },
            ]}
            onChange={(key) => {
              if (key === 'login') navigate('/login');
            }}
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

          <form onSubmit={registerForm.handleSubmit(handleRegister)} className="space-y-4">
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
              htmlType="submit"
              className="w-full h-11 text-lg"
              loading={isLoading}
              style={{ borderRadius: 8 }}
            >
              Create Account
            </Button>
          </form>

          <p className="text-center text-sm text-[var(--color-text-secondary)] mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-500 font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}