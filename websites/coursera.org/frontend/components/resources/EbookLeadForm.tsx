"use client";

import { useMemo, useState } from "react";
import { apiPost } from "@/lib/api";

type Props = {
  resourceSlug: string;
};

type Status = "idle" | "submitting" | "success" | "error";

export function EbookLeadForm({ resourceSlug }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  const disciplines = useMemo(
    () => [
      "Business",
      "Computer Science",
      "Data Science",
      "Engineering",
      "Health",
      "Humanities",
      "Social Sciences",
      "Other",
    ],
    [],
  );

  const countries = useMemo(
    () => [
      { code: "US", name: "United States" },
      { code: "CA", name: "Canada" },
      { code: "GB", name: "United Kingdom" },
      { code: "AU", name: "Australia" },
      { code: "DE", name: "Germany" },
      { code: "FR", name: "France" },
      { code: "IN", name: "India" },
      { code: "BR", name: "Brazil" },
      { code: "MX", name: "Mexico" },
      { code: "JP", name: "Japan" },
      { code: "KR", name: "South Korea" },
      { code: "SG", name: "Singapore" },
    ],
    [],
  );

  async function onSubmit(formData: FormData) {
    setStatus("submitting");
    setError(null);

    const payload = {
      resource_slug: resourceSlug,
      first_name: String(formData.get("first_name") ?? "").trim(),
      last_name: String(formData.get("last_name") ?? "").trim(),
      job_title: String(formData.get("job_title") ?? "").trim(),
      work_email: String(formData.get("work_email") ?? "").trim(),
      work_phone: String(formData.get("work_phone") ?? "").trim(),
      institution_name: String(formData.get("institution_name") ?? "").trim(),
      primary_discipline: String(formData.get("primary_discipline") ?? "").trim(),
      country: String(formData.get("country") ?? "").trim(),
      consent_text:
        "By submitting your info in the form above, you agree to our Terms of Use and Privacy Notice. We may use this info to contact you.",
    };

    // Basic client-side validation (mirrors required asterisks in reference)
    const requiredKeys: (keyof typeof payload)[] = [
      "first_name",
      "last_name",
      "job_title",
      "work_email",
      "work_phone",
      "institution_name",
      "primary_discipline",
      "country",
    ];
    for (const key of requiredKeys) {
      if (!payload[key]) {
        setStatus("error");
        setError("Please complete all required fields.");
        return;
      }
    }
    if (!/^\S+@\S+\.\S+$/.test(payload.work_email)) {
      setStatus("error");
      setError("Please enter a valid work email address.");
      return;
    }

    try {
      await apiPost<{ message: string }>("/api/leads/ebook", payload);
      setStatus("success");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Submission failed");
    }
  }

  return (
    <form
      action={async (fd) => onSubmit(fd)}
      className="rounded border border-zinc-200 bg-white p-6"
    >
      <div className="space-y-3">
        <Field label="First Name" name="first_name" required />
        <Field label="Last Name" name="last_name" required />
        <Field label="Job Title" name="job_title" required />
        <Field label="Work Email Address" name="work_email" required type="email" />
        <Field
          label="Work Phone Number"
          name="work_phone"
          required
          placeholder="Country Code + Phone Number"
        />
        <Field label="Institution Name" name="institution_name" required />

        <div>
          <Label label="Primary Discipline" required />
          <select
            name="primary_discipline"
            required
            className="mt-1 h-10 w-full rounded border border-zinc-300 px-3 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
            defaultValue=""
          >
            <option value="" disabled>
              Select...
            </option>
            {disciplines.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        <div>
          <Label label="Country" required />
          <select
            name="country"
            required
            className="mt-1 h-10 w-full rounded border border-zinc-300 px-3 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
            defaultValue=""
          >
            <option value="" disabled>
              Select...
            </option>
            {countries.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <p className="pt-2 text-[11px] leading-5 text-zinc-600">
          By submitting your info in the form above, you agree to our{" "}
          <a href="/terms" className="text-[#0056D2] hover:underline">
            Terms of Use
          </a>{" "}
          and{" "}
          <a href="/privacy" className="text-[#0056D2] hover:underline">
            Privacy Notice
          </a>
          . We may use this info to contact you and/or use data from third parties to personalize your experience.
        </p>

        <button
          type="submit"
          disabled={status === "submitting" || status === "success"}
          className="mt-2 inline-flex h-11 w-full items-center justify-center rounded bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8] disabled:opacity-60"
        >
          {status === "submitting" ? "Submitting..." : "Submit"}
        </button>

        {status === "success" ? (
          <div className="rounded bg-green-50 p-3 text-sm text-green-900">
            Submitted. Thanks! You can now download the report.
          </div>
        ) : null}
        {status === "error" && error ? (
          <div className="rounded bg-red-50 p-3 text-sm text-red-900">{error}</div>
        ) : null}
      </div>
    </form>
  );
}

function Label({ label, required }: { label: string; required?: boolean }) {
  return (
    <div className="text-[11px] font-semibold text-zinc-800">
      {required ? <span className="text-red-600">*</span> : null} {label}
    </div>
  );
}

function Field({
  label,
  name,
  required,
  placeholder,
  type = "text",
}: {
  label: string;
  name: string;
  required?: boolean;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <Label label={label} required={required} />
      <input
        name={name}
        type={type}
        required={required}
        placeholder={placeholder}
        className="mt-1 h-10 w-full rounded border border-zinc-300 px-3 text-sm text-zinc-800 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
      />
    </div>
  );
}

