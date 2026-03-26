import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "@/features/auth/components/LoginForm";

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
}));

const mockSignInWithEmailAndPassword = vi.fn();
const mockSignInWithPopup = vi.fn();
const mockCreateUserWithEmailAndPassword = vi.fn();

vi.mock("firebase/auth", () => ({
  signInWithEmailAndPassword: (...args: unknown[]) =>
    mockSignInWithEmailAndPassword(...args),
  signInWithPopup: (...args: unknown[]) => mockSignInWithPopup(...args),
  createUserWithEmailAndPassword: (...args: unknown[]) =>
    mockCreateUserWithEmailAndPassword(...args),
  GoogleAuthProvider: vi.fn(),
}));

vi.mock("@/lib/firebase", () => ({
  auth: {},
}));

const mockLoginToBackend = vi.fn();

vi.mock("@/features/auth/api/login", () => ({
  loginToBackend: (...args: unknown[]) => mockLoginToBackend(...args),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders login form with email and password fields", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText("メールアドレス")).toBeInTheDocument();
    expect(screen.getByLabelText("パスワード")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "ログイン" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Google でログイン/i }),
    ).toBeInTheDocument();
  });

  it("calls signInWithEmailAndPassword on valid login", async () => {
    const user = userEvent.setup();
    mockSignInWithEmailAndPassword.mockResolvedValue({
      user: { displayName: "Test User", photoURL: null },
    });
    mockLoginToBackend.mockResolvedValue({});

    render(<LoginForm />);

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockSignInWithEmailAndPassword).toHaveBeenCalled();
      expect(mockLoginToBackend).toHaveBeenCalledWith("Test User", null);
      expect(mockReplace).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("switches to register mode when clicking new registration link", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    const registerLink = screen.getByRole("button", { name: "新規登録" });
    await user.click(registerLink);

    expect(
      screen.getByRole("button", { name: "アカウント作成" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "ログイン" }),
    ).toBeInTheDocument();
  });

  it("calls createUserWithEmailAndPassword in register mode", async () => {
    const user = userEvent.setup();
    mockCreateUserWithEmailAndPassword.mockResolvedValue({
      user: { displayName: null, photoURL: null },
    });
    mockLoginToBackend.mockResolvedValue({});

    render(<LoginForm />);

    const registerLink = screen.getByRole("button", { name: "新規登録" });
    await user.click(registerLink);

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "アカウント作成" });

    await user.type(emailInput, "new@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockCreateUserWithEmailAndPassword).toHaveBeenCalled();
      expect(mockLoginToBackend).toHaveBeenCalled();
      expect(mockReplace).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows error message on invalid credentials", async () => {
    const user = userEvent.setup();
    mockSignInWithEmailAndPassword.mockRejectedValue({
      code: "auth/invalid-credential",
    });

    render(<LoginForm />);

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "wrongpassword");
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("メールアドレスまたはパスワードが正しくありません"),
      ).toBeInTheDocument();
    });
  });

  it("shows error message when user not found", async () => {
    const user = userEvent.setup();
    mockSignInWithEmailAndPassword.mockRejectedValue({
      code: "auth/user-not-found",
    });

    render(<LoginForm />);

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "ログイン" });

    await user.type(emailInput, "notfound@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("ユーザーが見つかりません")).toBeInTheDocument();
    });
  });

  it("shows error message when email already in use", async () => {
    const user = userEvent.setup();
    mockCreateUserWithEmailAndPassword.mockRejectedValue({
      code: "auth/email-already-in-use",
    });

    render(<LoginForm />);

    const registerLink = screen.getByRole("button", { name: "新規登録" });
    await user.click(registerLink);

    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");
    const submitButton = screen.getByRole("button", { name: "アカウント作成" });

    await user.type(emailInput, "existing@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("このメールアドレスは既に使用されています"),
      ).toBeInTheDocument();
    });
  });

  it("calls Google login on button click", async () => {
    const user = userEvent.setup();
    mockSignInWithPopup.mockResolvedValue({
      user: { displayName: "Google User", photoURL: "https://example.com/photo.jpg" },
    });
    mockLoginToBackend.mockResolvedValue({});

    render(<LoginForm />);

    const googleButton = screen.getByRole("button", {
      name: /Google でログイン/i,
    });
    await user.click(googleButton);

    await waitFor(() => {
      expect(mockSignInWithPopup).toHaveBeenCalled();
      expect(mockLoginToBackend).toHaveBeenCalledWith(
        "Google User",
        "https://example.com/photo.jpg",
      );
      expect(mockReplace).toHaveBeenCalledWith("/dashboard");
    });
  });
});
