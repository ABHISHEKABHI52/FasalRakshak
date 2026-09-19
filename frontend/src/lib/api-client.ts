/**
 * Typed API client (docs/05 §1.3).
 *
 * - single place that knows the API base URL and the error envelope
 * - normalises backend errors into ApiError with a localisable message key
 * - supports request cancellation/timeout without hiding failures
 */

import { env } from "@/lib/env";
import type {
  ApiErrorEnvelope,
  HealthDto,
  ReadinessDto,
  RegisterResponseDto,
  TokenResponseDto,
  UserDto,
} from "@/types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly messageKey: string;
  readonly details: ApiErrorEnvelope["details"];

  constructor(status: number, envelope: ApiErrorEnvelope) {
    super(envelope.message_key);
    this.name = "ApiError";
    this.status = status;
    this.code = envelope.code;
    this.messageKey = envelope.message_key;
    this.details = envelope.details;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
  timeoutMs?: number;
}

const DEFAULT_TIMEOUT_MS = 15_000;

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token, timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${env.apiUrl}/api/v1${path}`, {
      method,
      headers: {
        Accept: "application/json",
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
      credentials: "include", // refresh cookie is httpOnly + scoped (docs/12 §1)
    });

    if (response.status === 204) {
      return undefined as T;
    }

    const payload: unknown = await response.json().catch(() => null);

    if (!response.ok) {
      const envelope: ApiErrorEnvelope =
        payload && typeof payload === "object" && "code" in payload
          ? (payload as ApiErrorEnvelope)
          : { code: "internal_error", message_key: "errors.internal_error" };
      throw new ApiError(response.status, envelope);
    }

    return payload as T;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  health: () => request<HealthDto>("/health"),
  ready: () => request<ReadinessDto>("/ready"),

  auth: {
    register: (input: {
      phone: string;
      password: string;
      full_name: string;
      preferred_language?: string;
      district?: string | null;
      state?: string | null;
      consent_ml_use?: boolean;
    }) => request<RegisterResponseDto>("/auth/register", { method: "POST", body: input }),

    login: (input: { phone_or_email: string; password: string }) =>
      request<TokenResponseDto>("/auth/login", { method: "POST", body: input }),

    me: (token: string) => request<UserDto>("/auth/me", { token }),

    refresh: () => request<TokenResponseDto>("/auth/refresh", { method: "POST" }),

    logout: () => request<void>("/auth/logout", { method: "POST" }),
  },
};