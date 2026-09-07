"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const team = [
  {
    name: "Алексей Леонидович",
    role: "CEO & Sales Architect",
    bio: "12+ лет в B2B продажах. Создал Джарвис — AI-ассистента для управления сделками в Telegram. Специализируется на автоматизации продаж в HoReCa, логистике и IT.",
    skills: ["B2B продажи", "AI-архитектура", "CRM-дизайн", "Telegram Bot"],
    emoji: "👨‍💼",
    linkedIn: "#",
  },
  {
    name: "Юлия",
    role: "Head of Client Success",
    bio: "Ведёт ключевых клиентов от онбординга до расширения контракта. Специализируется на внедрении AI-решений в действующие отделы продаж.",
    skills: ["Account Management", "Onboarding", "B2B Kwork", "Продажи SaaS"],
    emoji: "👩‍💻",
    linkedIn: "#",
  },
];

export default function Team() {
  const headRef = useRef(null);
  const headInView = useInView(headRef, { once: true, margin: "-80px" });
  const gridRef = useRef(null);
  const gridInView = useInView(gridRef, { once: true, margin: "-80px" });

  return (
    <section id="team" className="py-28 px-6">
      <div className="max-w-5xl mx-auto">
        <div ref={headRef} className="text-center mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            animate={headInView ? { opacity: 1 } : {}}
            className="text-[#D4A017] text-xs font-bold uppercase tracking-[0.2em] mb-5 block"
          >
            Команда
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.1, duration: 0.6 }}
            className="text-4xl lg:text-5xl font-black"
          >
            Люди за{" "}
            <span className="text-gradient">ST8-AI</span>
          </motion.h2>
        </div>

        <div ref={gridRef} className="grid md:grid-cols-2 gap-6">
          {team.map((m, i) => (
            <motion.div
              key={m.name}
              initial={{ opacity: 0, y: 50 }}
              animate={gridInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.2, duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
              className="group bg-white/[0.03] border border-white/8 rounded-3xl p-8 hover:border-[#D4A017]/30 transition-all duration-400"
            >
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-[#D4A017]/10 border border-[#D4A017]/20 rounded-2xl flex items-center justify-center text-3xl group-hover:bg-[#D4A017]/20 transition-colors">
                  {m.emoji}
                </div>
                <div>
                  <h3 className="font-black text-lg group-hover:text-[#D4A017] transition-colors">{m.name}</h3>
                  <p className="text-[#D4A017]/70 text-sm">{m.role}</p>
                </div>
              </div>

              <p className="text-white/55 text-sm leading-relaxed mb-6">{m.bio}</p>

              <div className="flex flex-wrap gap-2">
                {m.skills.map((s) => (
                  <span
                    key={s}
                    className="px-3 py-1 bg-white/[0.04] border border-white/8 rounded-full text-white/50 text-xs hover:border-[#D4A017]/30 hover:text-[#D4A017]/70 transition-colors"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
