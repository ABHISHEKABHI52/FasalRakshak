/** Minimal design-system primitives (docs/14 §5). Phase 1: no page-specific widgets. */

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

const BUTTON_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-field-600 text-white hover:bg-field-700 focus-visible:outline-field-700",
  secondary: "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50",
  ghost: "text-field-700 hover:bg-field-50",
};

type ButtonSize = "sm" | "md";

const BUTTON_SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: "px-2 py-1 text-xs",
  md: "px-4 py-2 text-sm",
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize; children: ReactNode }) {
  return (
    <button
            className={`inline-flex items-center justify-center gap-2 rounded-md font-medium transition disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${BUTTON_CLASSES[variant]} ${BUTTON_SIZE_CLASSES[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input({
  label,
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label?: string; className?: string }) {
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {label && <label className="text-sm font-medium text-slate-700">{label}</label>}
      <input
        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus-visible:border-field-600 focus-visible:outline-none"
        {...props}
      />
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "info";
}) {
  const tones = {
    neutral: "bg-slate-100 text-slate-700",
    success: "bg-green-100 text-green-800",
    warning: "bg-amber-100 text-amber-800",
    info: "bg-sky-100 text-sky-800",
  } as const;
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}