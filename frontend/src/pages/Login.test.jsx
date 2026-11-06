import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Login from "./Login";

const { login, register } = vi.hoisted(() => ({
  login: vi.fn(),
  register: vi.fn(),
}));

vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ login, register }),
}));

describe("Login", () => {
  beforeEach(() => {
    login.mockReset();
    register.mockReset().mockResolvedValue({ role: "student" });
  });

  it("allows a student to register and redirects to their dashboard", async () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/student" element={<div>Student dashboard</div>} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Create a student account" }));
    fireEvent.change(screen.getByLabelText("Full name"), { target: { value: "New Student" } });
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "student@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "StudentPass!2026" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account", exact: false }));

    await waitFor(() => expect(register).toHaveBeenCalledWith(
      "New Student",
      "student@example.com",
      "StudentPass!2026",
      "ta",
    ));
    expect(await screen.findByText("Student dashboard")).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });
});
