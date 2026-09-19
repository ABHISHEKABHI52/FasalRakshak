/** API contract types — mirrors backend Pydantic schemas (docs/08 §11). */

/** Stable error envelope returned by the backend for every failure. */
export interface ApiErrorEnvelope {
  code: string;
  message_key: string;
  details?: {
    fields?: Array<{ field: string; message: string }>;
    required_roles?: string[];
    retry_after_seconds?: number;
    [key: string]: unknown;
  };
}

export type RoleName = "FARMER" | "EXTENSION_WORKER" | "EXPERT" | "OFFICER" | "ADMIN";

export interface UserDto {
  id: string;
  phone: string;
  email: string | null;
  full_name: string;
  preferred_language: string;
  district: string | null;
  state: string | null;
  consent_ml_use: boolean;
  roles: RoleName[];
  created_at: string;
}

export interface TokenResponseDto {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserDto;
}

export interface RegisterResponseDto {
  user_id: string;
  roles: RoleName[];
}

export interface HealthDto {
  status: string;
  app: string;
}

export interface ReadinessDto {
  db: boolean;
}