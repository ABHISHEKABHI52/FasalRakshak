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
  FarmDto,
  FarmCreate,
  FarmUpdate,
  FieldDto,
  FieldCreate,
  FieldUpdate,
  CropDto,
  CropCycleDto,
  CropCycleCreate,
  CropCycleUpdate,
  ScanDto,
  ScanCreate,
  ScanListDto,
  ImageUploadResponseDto,
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
  formData?: boolean;
}

const DEFAULT_TIMEOUT_MS = 15_000;

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = "GET",
    body,
    token,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    formData = false,
  } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    let bodyArg: string | FormData | undefined;

    if (formData) {
      if (body) {
        headers["Content-Type"] = "multipart/form-data";
        bodyArg = body as FormData;
      }
    } else {
      if (body) {
        headers["Content-Type"] = "application/json";
        bodyArg = JSON.stringify(body);
      }
    }
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${env.apiUrl}/api/v1${path}`, {
      method,
      headers,
      body: bodyArg,
      signal: controller.signal,
      credentials: "include",
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

  farms: {
    list: (token: string) => request<FarmDto[]>("/farms", { token }),
    create: (token: string, input: FarmCreate) =>
      request<FarmDto>("/farms", { method: "POST", body: input, token }),
    get: (token: string, farmId: string) =>
      request<FarmDto>(`/farms/${farmId}`, { token }),
    update: (token: string, farmId: string, input: FarmUpdate) =>
      request<FarmDto>(`/farms/${farmId}`, { method: "PATCH", body: input, token }),
    archive: (token: string, farmId: string) =>
      request<void>(`/farms/${farmId}`, { method: "DELETE", token }),
  },

  fields: {
    list: (token: string, farmId: string) =>
      request<FieldDto[]>(`/fields?farm_id=${encodeURIComponent(farmId)}`, { token }),
    create: (token: string, input: FieldCreate) =>
      request<FieldDto>("/fields", { method: "POST", body: input, token }),
    get: (token: string, fieldId: string) =>
      request<FieldDto>(`/fields/${fieldId}`, { token }),
    update: (token: string, fieldId: string, input: FieldUpdate) =>
      request<FieldDto>(`/fields/${fieldId}`, { method: "PATCH", body: input, token }),
    archive: (token: string, fieldId: string) =>
      request<void>(`/fields/${fieldId}`, { method: "DELETE", token }),
  },

  crops: {
    list: (token: string) => request<CropDto[]>("/crops", { token }),
  },

  cropCycles: {
    list: (token: string, fieldId: string) =>
      request<CropCycleDto[]>(`/crop-cycles?field_id=${encodeURIComponent(fieldId)}`, { token }),
    create: (token: string, input: CropCycleCreate) =>
      request<CropCycleDto>("/crop-cycles", { method: "POST", body: input, token }),
    get: (token: string, cycleId: string) =>
      request<CropCycleDto>(`/crop-cycles/${cycleId}`, { token }),
    update: (token: string, cycleId: string, input: CropCycleUpdate) =>
      request<CropCycleDto>(`/crop-cycles/${cycleId}`, { method: "PATCH", body: input, token }),
  },

  scans: {
    list: (token: string) => request<ScanListDto>("/scans", { token }),
    listByField: (token: string, fieldId: string) =>
      request<ScanListDto>(`/scans?field_id=${encodeURIComponent(fieldId)}`, { token }),
    create: (token: string, input: ScanCreate) =>
      request<ScanDto>("/scans", { method: "POST", body: input, token }),
    get: (token: string, scanId: string) =>
      request<ScanDto>(`/scans/${scanId}`, { token }),
    uploadImage: (token: string, scanId: string, file: File, filename: string) => {
      const form = new FormData();
      form.append("image", file, filename);
      return request<ImageUploadResponseDto>(
        `/scans/${scanId}/image`,
        { method: "POST", formData: true, body: form, token },
      );
    },
  },
};