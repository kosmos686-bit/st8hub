"use server";

import {
  leadSchema,
  LEAD_HONEYPOT_FIELD,
  LEAD_CONSENT_FIELD,
} from "@/lib/validation/lead";

export interface LeadFormState {
  status: "idle" | "success" | "error";
  fieldErrors?: Record<string, string[]>;
}

export async function submitLeadForm(
  _prevState: LeadFormState,
  formData: FormData
): Promise<LeadFormState> {
  const honeypot = formData.get(LEAD_HONEYPOT_FIELD);
  if (typeof honeypot === "string" && honeypot.trim() !== "") {
    return { status: "success" };
  }

  const consent = formData.get(LEAD_CONSENT_FIELD);
  if (consent !== "on") {
    return {
      status: "error",
      fieldErrors: {
        consent: ["Нужно согласие на обработку персональных данных"],
      },
    };
  }

  const parsed = leadSchema.safeParse({
    name: formData.get("name"),
    phone: formData.get("phone"),
    company: formData.get("company"),
  });

  if (!parsed.success) {
    return {
      status: "error",
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  // No lead-storage backend chosen yet — log locally until one is wired up.
  console.log("[lead] new request:", parsed.data);

  return { status: "success" };
}
