import Link from "next/link";
import { Mail, Phone, Send } from "lucide-react";
import { TELEGRAM_URL } from "@/lib/constants";

const solutionLinks = [
  { label: "HoReCa", href: "/#solutions" },
  { label: "Производство", href: "/#solutions" },
  { label: "Ритейл", href: "/#solutions" },
  { label: "Логистика", href: "/#solutions" },
  { label: "Офисы и УК", href: "/#solutions" },
];

const companyLinks = [
  { label: "О нас", href: "/about" },
  { label: "Кейсы", href: "/cases" },
  { label: "Блог", href: "/blog" },
];

export function Footer() {
  return (
    <footer id="contact" className="border-t border-white/6 bg-background">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-16 text-sm sm:grid-cols-2 md:grid-cols-[2fr_1fr_1fr_1fr] md:px-12 md:py-20">
        <div className="max-w-xs">
          <div className="mb-4 text-lg font-semibold tracking-tight">
            ST8<span className="text-gold">-AI</span>
          </div>
          <p className="mb-5 leading-relaxed text-foreground/50">
            Кастомные AI-решения для бизнеса. 47 проектов, 0 провалов. Гарантия
            результата по договору.
          </p>
          <div className="flex gap-3">
            <a
              href={TELEGRAM_URL}
              target="_blank"
              rel="noopener"
              aria-label="Telegram"
              className="flex h-10 w-10 items-center justify-center rounded-full border border-white/8 bg-white/[0.02] text-foreground transition-colors hover:border-gold/30 hover:text-gold"
            >
              <Send className="h-[18px] w-[18px]" />
            </a>
            <a
              href="tel:+79856905252"
              aria-label="Телефон"
              className="flex h-10 w-10 items-center justify-center rounded-full border border-white/8 bg-white/[0.02] text-foreground transition-colors hover:border-gold/30 hover:text-gold"
            >
              <Phone className="h-[18px] w-[18px]" />
            </a>
            <a
              href="mailto:info@st8-ai.ru"
              aria-label="Email"
              className="flex h-10 w-10 items-center justify-center rounded-full border border-white/8 bg-white/[0.02] text-foreground transition-colors hover:border-gold/30 hover:text-gold"
            >
              <Mail className="h-[18px] w-[18px]" />
            </a>
          </div>
        </div>

        <div>
          <div className="mb-5 text-xs font-semibold uppercase tracking-wide text-foreground/40">
            Решения
          </div>
          <ul className="space-y-3 text-foreground/60">
            {solutionLinks.map((l, i) => (
              <li key={`${l.label}-${i}`}>
                <Link href={l.href} className="transition-colors hover:text-gold">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="mb-5 text-xs font-semibold uppercase tracking-wide text-foreground/40">
            Компания
          </div>
          <ul className="space-y-3 text-foreground/60">
            {companyLinks.map((l) => (
              <li key={l.label}>
                <Link href={l.href} className="transition-colors hover:text-gold">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="mb-5 text-xs font-semibold uppercase tracking-wide text-foreground/40">
            Контакты
          </div>
          <div className="space-y-3 leading-relaxed text-foreground/60">
            <p>
              <strong className="text-foreground">Алексей Гагарин</strong>
              <br />
              CEO & Co-founder
            </p>
            <p>
              <a href="tel:+79856905252" className="hover:text-gold">
                +7 985 690-52-52
              </a>
              <br />
              <a
                href={TELEGRAM_URL}
                target="_blank"
                rel="noopener"
                className="hover:text-gold"
              >
                @Zzima686
              </a>
            </p>
            <p>
              <strong className="text-foreground">Юлия Попова</strong>
              <br />
              Co-founder
              <br />
              <a href="tel:+79826210101" className="hover:text-gold">
                +7 982 621-01-01
              </a>
            </p>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl border-t border-white/6 px-6 py-6 text-xs text-foreground/30 md:px-12">
        {/* Реквизиты — заглушка, ждём данных от заказчика */}
        <p className="mb-3">
          [Наименование ЮЛ — уточняется] · ИНН [уточняется] · ОГРН
          [уточняется] · [юридический адрес — уточняется]
        </p>
        <div className="flex flex-col items-center gap-2 sm:flex-row sm:justify-between sm:text-left">
          <p>ST8 AI. Все права защищены.</p>
          <div className="flex gap-4">
            <Link href="/legal/privacy" className="hover:text-gold">
              Конфиденциальность
            </Link>
            <Link href="/legal/consent" className="hover:text-gold">
              Согласие на обработку ПД
            </Link>
          </div>
          <p>152-ФЗ | Гарантия KPI | Поддержка 24/7</p>
        </div>
      </div>
    </footer>
  );
}
