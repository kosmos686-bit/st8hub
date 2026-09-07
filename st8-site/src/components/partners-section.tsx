import { Handshake } from "lucide-react";
import { partners } from "@/lib/data/partners";

export function PartnersSection() {
  return (
    <div className="mx-auto grid max-w-sm gap-5">
      {partners.map((partner) => (
        <div
          key={partner.slug}
          className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card"
        >
          <div className="relative flex h-[140px] items-center justify-center border-b border-border bg-background">
            <span className="absolute left-3 top-3 rounded-full border border-gold/25 bg-gold/10 px-2.5 py-1 text-[9px] font-semibold uppercase tracking-wide text-gold">
              Партнёр
            </span>
            <Handshake className="h-10 w-10 text-gold/40" />
          </div>
          <div className="flex flex-1 flex-col p-6">
            <h3 className="mb-1 text-lg font-semibold">{partner.name}</h3>
            <p className="mb-3 text-[11px] uppercase tracking-wide text-gold/70">
              {partner.industry}
            </p>
            <p className="text-sm leading-relaxed text-foreground/60">
              {partner.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
