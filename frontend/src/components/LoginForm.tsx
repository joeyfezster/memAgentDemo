import { type FormEvent, useState } from "react";

type LoginFormProps = {
  onSubmit: (email: string, password: string) => Promise<void> | void;
  error?: string | null;
  loading?: boolean;
};

const initialForm = {
  email: "",
  password: "",
};

const initialErrors = {
  email: "",
  password: "",
};

const validateEmail = (value: string) =>
  /\S+@\S+\.\S+/.test(value) ? "" : "Enter a valid email address";

export default function LoginForm({
  onSubmit,
  error,
  loading = false,
}: LoginFormProps) {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState(initialErrors);
  const [submitted, setSubmitted] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitted(false);
    setSubmitError(null);

    const nextErrors = {
      email: validateEmail(form.email),
      password: form.password ? "" : "Password is required",
    };

    setErrors(nextErrors);
    const hasErrors = Object.values(nextErrors).some(Boolean);

    if (!hasErrors) {
      try {
        await onSubmit(form.email, form.password);
        setSubmitted(true);
      } catch (submissionError) {
        if (submissionError instanceof Error) {
          setSubmitError(submissionError.message);
        } else {
          setSubmitError("Unable to sign in");
        }
      }
    }
  };

  return (
    <form className="login" onSubmit={handleSubmit} noValidate>
      <label className="login__label" htmlFor="email">
        Email
      </label>
      <input
        id="email"
        name="email"
        type="email"
        autoComplete="email"
        value={form.email}
        onChange={(event) => {
          const { value } = event.target;
          setForm((current) => ({ ...current, email: value }));
        }}
        aria-describedby="email-error"
        required
      />
      {errors.email && (
        <p className="login__error" id="email-error">
          {errors.email}
        </p>
      )}

      <label className="login__label" htmlFor="password">
        Password
      </label>
      <input
        id="password"
        name="password"
        type="password"
        autoComplete="current-password"
        value={form.password}
        onChange={(event) => {
          const { value } = event.target;
          setForm((current) => ({ ...current, password: value }));
        }}
        aria-describedby="password-error"
        required
      />
      {errors.password && (
        <p className="login__error" id="password-error">
          {errors.password}
        </p>
      )}

      <button className="login__submit" type="submit" disabled={loading}>
        {loading ? "Signing in..." : "Sign in"}
      </button>

      {(error || submitError) && (
        <p aria-live="assertive" role="alert" className="login__status login__status--error">
          {error ?? submitError}
        </p>
      )}

      {submitted && !error && !submitError && (
        <p aria-live="polite" role="status" className="login__status">
          You are signed in. Agent workspace coming soon!
        </p>
      )}
    </form>
  );
}
