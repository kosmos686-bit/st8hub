"use server";

import {
  contactSchema,
  HONEYPOT_FIELD,
  CONSENT_FIELD,
} from "@/lib/validation/contact";

export interface ContactFormState {
  status: "idle" | "success" | "error";
  fieldErrors?: Record<string, string[]>;
}

export async function submitContactForm(
  _prevState: ContactFormState,
  formData: FormData
): Promise<ContactFormState> {
  // Honeypot: hidden field real users never fill in. If it's set, pretend
  // success without processing anything — no need to tip off the bot.
  const honeypot = formData.get(HONEYPOT_FIELD);
  if (typeof honeypot === "string" && honeypot.trim() !== "") {
    return { status: "success" };
  }

  const consent = formData.get(CONSENT_FIELD);
  if (consent !== "on") {
    return {
      status: "error",
      fieldErrors: {
        consent: ["Нужно согласие на обработку персональных данных"],
      },
    };
  }

  const parsed = contactSchema.safeParse({
    name: formData.get("name"),
    contact: formData.get("contact"),
    message: formData.get("message"),
  });

  if (!parsed.success) {
    return {
      status: "error",
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  // No lead-storage backend chosen yet — log locally until one is wired up.
  console.log("[contact] new lead:", parsed.data);

  return { status: "success" };
}
