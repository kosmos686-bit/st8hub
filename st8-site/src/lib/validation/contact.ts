import { z } from "zod";

export const contactSchema = z.object({
  name: z.string().trim().min(2, "Введите имя").max(100, "Слишком длинное имя"),
  contact: z
    .string()
    .trim()
    .min(3, "Введите Telegram или телефон")
    .max(150, "Слишком длинное значение"),
  message: z
    .string()
    .trim()
    .min(10, "Опишите задачу подробнее")
    .max(2000, "Слишком длинное сообщение"),
});

export type ContactFormValues = z.infer<typeof contactSchema>;

export const HONEYPOT_FIELD = "company_website";
export const CONSENT_FIELD = "consent";
