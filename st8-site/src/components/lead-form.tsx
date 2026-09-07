"use client";

import { useActionState, useEffect, useState } from "react";
import Link from "next/link";
import { Send } from "lucide-react";
import ParticleButton from "@/components/kokonutui/particle-button";
import { TELEGRAM_URL } from "@/lib/constants";
import {
  LEAD_HONEYPOT_FIELD,
  LEAD_CONSENT_FIELD,
} from "@/lib/validation/lead";
import { submitLeadForm, type LeadFormState } from "@/app/lead-actions";

const initialState: LeadFormState = { status: "idle" };

export function LeadForm() {
  const [state, formAction, pending] = useActionState(
    submitLeadForm,
    initialState
  );
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (state.status === "success") {
      setSent(true);
    }
  }, [state.status]);

  const errors = state.fieldErrors ?? {};

  if (sent) {
    return (
      <div className="mx-auto max-w-md rounded-2xl border border-gold/20 bg-gold/5 p-8 text-center">
        <p className="text-lg font-semibold">Заявка получена</p>
        <p className="mt-2 text-sm text-foreground/60">
          Свяжемся с вами в течение рабочего дня.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md">
      <form action={formAction} className="flex flex-col gap-4">
        <input
          type="text"
          name={LEAD_HONEYPOT_FIELD}
          tabIndex={-1}
          autoComplete="off"
          aria-hidden="true"
          className="absolute h-0 w-0 opacity-0"
          style={{ left: "-9999px" }}
        />

        <div>
          <input
            required
            name="name"
            placeholder="Ваше имя"
            className="w-full rounded-lg border border-input bg-background px-4 py-3 text-sm outline-none focus:border-gold"
          />
          {errors.name && (
            <p className="mt-1 text-xs text-destructive">{errors.name[0]}</p>
          )}
        </div>

        <div>
          <input
            required
            type="tel"
            name="phone"
            placeholder="Телефон"
            className="w-full rounded-lg border border-input bg-background px-4 py-3 text-sm outline-none focus:border-gold"
          />
          {errors.phone && (
            <p className="mt-1 text-xs text-destructive">{errors.phone[0]}</p>
          )}
        </div>

        <div>
          <input
            name="company"
            placeholder="Компания (необязательно)"
            className="w-full rounded-lg border border-input bg-background px-4 py-3 text-sm outline-none focus:border-gold"
          />
        </div>

        <div>
          <label className="flex items-start gap-2.5 text-xs text-foreground/60">
            <input
              required
              type="checkbox"
              name={LEAD_CONSENT_FIELD}
              defaultChecked={false}
              className="mt-0.5 h-4 w-4 shrink-0 accent-gold"
            />
            <span>
              Согласен на обработку персональных данных в соответствии с{" "}
              <Link href="/legal/privacy" className="underline hover:text-gold">
                политикой конфиденциальности
              </Link>
            </span>
          </label>
          {errors.consent && (
            <p className="mt-1 text-xs text-destructive">{errors.consent[0]}</p>
          )}
        </div>

        <ParticleButton
          type="submit"
          disabled={pending}
          className="mt-2 w-full bg-gold text-[#0a0a0a] hover:bg-gold/90"
        >
          {pending ? "Отправка…" : "Оставить заявку"}
        </ParticleButton>
      </form>

      <div className="mt-5 text-center text-sm text-foreground/50">
        или{" "}
        <Link
          href={TELEGRAM_URL}
          target="_blank"
          rel="noopener"
          className="inline-flex items-center gap-1.5 text-gold hover:text-gold/80"
        >
          <Send className="h-3.5 w-3.5" />
          напишите в Telegram
        </Link>
      </div>
    </div>
  );
}
