import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { WelcomeCard } from "@/features/dashboard/components/WelcomeCard";

describe("WelcomeCard", () => {
  it("renders welcome message", () => {
    render(<WelcomeCard />);

    expect(screen.getByText("AudienceRoom へようこそ")).toBeInTheDocument();
  });

  it("renders call to action button", () => {
    render(<WelcomeCard />);

    const button = screen.getByRole("link", { name: "最初の練習を始める" });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("href", "/sessions/new");
  });

  it("renders encouraging message", () => {
    render(<WelcomeCard />);

    expect(
      screen.getByText("練習は何度でもやり直せます。気軽に始めてみましょう。"),
    ).toBeInTheDocument();
  });
});
