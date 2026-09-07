import { z } from "zod";

export const leadSchema = z.object({
  name: z.string().trim().min(2, "Введите имя").max(100, "Слишком длинное имя"),
  phone: z
    .string()
    .trim()
    .min(5, "Введите телефон")
    .max(30, "Слишком длинный номер"),
  company: z
    .string()
    .trim()
    .max(150, "Слишком длинное название")
    .optional()
    .or(z.literal("")),
});

export type LeadFormValues = z.infer<typeof leadSchema>;

export const LEAD_HONEYPOT_FIELD = "website";
export const LEAD_CONSENT_FIELD = "consent";
