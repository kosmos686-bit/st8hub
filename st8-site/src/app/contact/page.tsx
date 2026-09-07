import type { Metadata } from "next";
import { ContactForm } from "./contact-form";

export const metadata: Metadata = {
  title: "Контакты",
  description: "Свяжитесь с ST8-AI, чтобы обсудить AI-автоматизацию вашего бизнеса.",
};

export default function ContactPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-xl">
        <h1 className="text-3xl font-semibold tracking-tight">Связаться с нами</h1>
        <p className="mt-3 text-foreground/70">
          Расскажите о задаче — ответим в течение рабочего дня.
        </p>
        <div className="mt-10">
          <ContactForm />
        </div>
      </div>
    </section>
  );
}
