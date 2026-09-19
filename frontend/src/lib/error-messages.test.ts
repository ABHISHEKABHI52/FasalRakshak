import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api-client";
import { friendlyMessage } from "@/lib/error-messages";

describe("friendlyMessage", () => {
  it("maps backend message keys to farmer-facing text", () => {
    const error = new ApiError(409, {
      code: "duplicate_phone",
      message_key: "errors.duplicate_phone",
    });
    expect(friendlyMessage(error)).toMatch(/already registered/i);
  });

  it("maps invalid credentials without revealing which factor failed", () => {
    const error = new ApiError(401, {
      code: "invalid_credentials",
      message_key: "errors.invalid_credentials",
    });
    expect(friendlyMessage(error)).toMatch(/phone number or password is incorrect/i);
  });

  it("falls back to a generic message for unknown failures", () => {
    expect(friendlyMessage(null)).toMatch(/try again/i);
    expect(friendlyMessage(new Error("boom"))).toMatch(/try again/i);
  });
});