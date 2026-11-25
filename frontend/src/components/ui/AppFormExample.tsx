import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Card, message } from "antd";
import {
  AppInput,
  AppTextArea,
  AppPasswordInput,
  AppConfirmPasswordInput,
  AppSelect,
} from "./index";

/**
 * Example showing how to use the new controlled input components with proper validation
 */

const exampleSchema = z
  .object({
    // Basic text input
    fullName: z.string().min(2, "Name must be at least 2 characters"),

    // Email with validation
    email: z.string().email("Invalid email address"),

    // Password with strength requirements
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),

    // Confirm password - validated against password field
    confirmPassword: z.string(),

    // Textarea
    bio: z.string().max(500, "Bio must be less than 500 characters").optional(),

    // Select
    role: z.enum(["user", "admin", "moderator"], {
      errorMap: () => ({ message: "Please select a valid role" }),
    }),

    // Multi-select
    interests: z.array(z.string()).optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type ExampleForm = z.infer<typeof exampleSchema>;

const ROLE_OPTIONS = [
  { value: "user", label: "User" },
  { value: "admin", label: "Admin" },
  { value: "moderator", label: "Moderator" },
];

const INTEREST_OPTIONS = [
  { value: "tech", label: "Technology" },
  { value: "design", label: "Design" },
  { value: "marketing", label: "Marketing" },
  { value: "writing", label: "Writing" },
  { value: "photography", label: "Photography" },
];

export function AppFormExample() {
  const form = useForm<ExampleForm>({
    resolver: zodResolver(exampleSchema),
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
      bio: "",
      role: "user",
      interests: [],
    },
    mode: "onBlur", // Validate on blur
  });

  const onSubmit = async (values: ExampleForm) => {
    console.log("Form submitted:", values);
    message.success("Form submitted successfully!");
    console.log(values);
  };

  return (
    <Card style={{ borderRadius: 12, maxWidth: 600, margin: "0 auto" }}>
      <div className="p-6 space-y-6">
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
          Form Example with Controlled Inputs
        </h2>
        <p className="text-[var(--color-text-secondary)]">
          This demonstrates the reusable AppInput, AppPasswordInput,
          AppConfirmPasswordInput, AppTextArea, and AppSelect components with
          proper validation.
        </p>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Full Name */}
          <AppInput<ExampleForm>
            control={form.control}
            name="fullName"
            label="Full Name"
            placeholder="John Doe"
            required
            autoComplete="name"
            prefix={<span>👤</span>}
          />

          {/* Email */}
          <AppInput<ExampleForm>
            control={form.control}
            name="email"
            label="Email Address"
            type="email"
            placeholder="you@example.com"
            required
            autoComplete="email"
            prefix={<span>✉️</span>}
          />

          {/* Password */}
          <AppPasswordInput<ExampleForm>
            control={form.control}
            name="password"
            label="Password"
            placeholder="••••••••"
            required
            autoComplete="new-password"
            prefix={<span>🔒</span>}
            helpText="Must be at least 8 characters with uppercase, lowercase, and number"
          />

          {/* Confirm Password */}
          <AppConfirmPasswordInput<ExampleForm>
            control={form.control}
            name="confirmPassword"
            matchField="password"
            label="Confirm Password"
            placeholder="••••••••"
            required
            autoComplete="new-password"
            prefix={<span>🔒</span>}
          />

          {/* Bio - Textarea */}
          <AppTextArea<ExampleForm>
            control={form.control}
            name="bio"
            label="Bio"
            placeholder="Tell us about yourself..."
            rows={4}
            autoSize={{ minRows: 3, maxRows: 6 }}
            helpText="Maximum 500 characters"
          />

          {/* Role - Select */}
          <AppSelect<ExampleForm>
            control={form.control}
            name="role"
            label="Role"
            placeholder="Select your role"
            required
            options={ROLE_OPTIONS}
          />

          {/* Interests - Multi Select */}
          <AppSelect<ExampleForm>
            control={form.control}
            name="interests"
            label="Interests"
            placeholder="Select your interests"
            options={INTEREST_OPTIONS}
            mode="multiple"
            maxTagCount={3}
            maxTagPlaceholder="selected"
          />

          <Button
            type="primary"
            htmlType="submit"
            className="w-full h-11 text-lg"
            style={{ borderRadius: 8 }}
          >
            Submit Form
          </Button>
        </form>
      </div>
    </Card>
  );
}
