"use client";

import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";
import ParticleButton from "@/components/kokonutui/particle-button";
import Link from "next/link";
import { HONEYPOT_FIELD, CONSENT_FIELD } from "@/lib/validation/contact";
import { submitContactForm, type ContactFormState } from "./actions";

const initialState: ContactFormState = { status: "idle" };

export function ContactForm() {
  const router = useRouter();
  const [state, formAction, pending] = useActionState(
    submitContactForm,
    initialState
  );

  useEffect(() => {
    if (state.status === "success") {
      router.push("/thank-you");
    }
  }, [state.status, router]);

  const errors = state.fieldErrors ?? {};

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {/* Honeypot — hidden from real users, left empty; bots tend to fill every field. */}
      <input
        type="text"
        name={HONEYPOT_FIELD}
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
          type="text"
          name="contact"
          placeholder="Telegram или телефон"
          className="w-full rounded-lg border border-input bg-background px-4 py-3 text-sm outline-none focus:border-gold"
        />
        {errors.contact && (
          <p className="mt-1 text-xs text-destructive">{errors.contact[0]}</p>
        )}
      </div>

      <div>
        <textarea
          required
          name="message"
          placeholder="Расскажите о задаче"
          rows={4}
          className="w-full rounded-lg border border-input bg-background px-4 py-3 text-sm outline-none focus:border-gold"
        />
        {errors.message && (
          <p className="mt-1 text-xs text-destructive">{errors.message[0]}</p>
        )}
      </div>

      <div>
        <label className="flex items-start gap-2.5 text-xs text-foreground/60">
          <input
            required
            type="checkbox"
            name={CONSENT_FIELD}
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
        {pending ? "Отправка…" : "Отправить"}
      </ParticleButton>
    </form>
  );
}
