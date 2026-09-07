const team = [
  {
    name: "Алексей Гагарин",
    role: "CEO & Co-founder",
    bio: "12+ лет в B2B продажах. Создал Джарвиса — AI-ассистента для управления сделками в Telegram. Специализируется на автоматизации продаж в HoReCa, логистике и IT.",
    skills: ["B2B продажи", "AI-архитектура", "CRM-дизайн", "Telegram Bot"],
  },
  {
    name: "Юлия Попова",
    role: "Co-founder",
    bio: "Ведёт ключевых клиентов от онбординга до расширения контракта. Специализируется на внедрении AI-решений в действующие отделы продаж.",
    skills: ["Account Management", "Onboarding", "Продажи SaaS"],
  },
];

export function TeamSection() {
  return (
    <div className="mx-auto grid max-w-3xl gap-5 md:grid-cols-2">
      {team.map((member) => (
        <div
          key={member.name}
          className="rounded-2xl border border-border bg-card p-7 transition-colors hover:border-gold/25"
        >
          <h3 className="text-lg font-semibold">{member.name}</h3>
          <p className="mb-4 text-sm text-gold/70">{member.role}</p>
          <p className="mb-5 text-sm leading-relaxed text-foreground/60">
            {member.bio}
          </p>
          <div className="flex flex-wrap gap-2">
            {member.skills.map((s) => (
              <span
                key={s}
                className="rounded-full border border-border bg-white/[0.02] px-3 py-1 text-xs text-foreground/50"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
