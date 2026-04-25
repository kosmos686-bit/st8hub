"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const pillars = [
  {
    icon: "🤖",
    title: "AI-первый подход",
    desc: "Автоматизируем рутину — менеджеры тратят время только на закрытие сделок, не на ввод данных.",
  },
  {
    icon: "📊",
    title: "Всё в одном экране",
    desc: "Лиды, статусы, следующие шаги, история — весь пайплайн в Telegram без CRM-усталости.",
  },
  {
    icon: "⚡",
    title: "Скорость реакции",
    desc: "AI-агент квалифицирует лид за секунды, отвечает 24/7, не теряет ни одной заявки.",
  },
];

export default function About() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="about" className="py-28 px-6">
      <div className="max-w-7xl mx-auto" ref={ref}>
        <div className="grid lg:grid-cols-2 gap-20 items-center">
          {/* Left */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          >
            <span className="text-[#D4A017] text-xs font-bold uppercase tracking-[0.2em] mb-5 block">
              О нас
            </span>
            <h2 className="text-4xl lg:text-5xl font-black leading-tight mb-7">
              Мы делаем AI-продажи{" "}
              <span className="text-gradient">реальностью</span>
            </h2>
            <p className="text-white/55 text-lg leading-relaxed mb-5">
              ST8-AI — команда из продавцов и инженеров. Мы знаем, как устроены B2B продажи в России, и создаём инструменты, которые реально работают в полях.
            </p>
            <p className="text-white/55 leading-relaxed mb-8">
              Наш флагман — <span className="text-white font-semibold">Джарвис</span>, AI-ассистент для управления продажами в Telegram. Он собирает лиды, квалифицирует, генерирует КП и ведёт пайплайн в режиме реального времени.
            </p>
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="text-3xl font-black text-[#D4A017]">2+</div>
                <div className="text-white/40 text-xs mt-1">года опыта</div>
              </div>
              <div className="w-px h-12 bg-white/10" />
              <div className="text-center">
                <div className="text-3xl font-black text-[#D4A017]">11</div>
                <div className="text-white/40 text-xs mt-1">активных клиентов</div>
              </div>
              <div className="w-px h-12 bg-white/10" />
              <div className="text-center">
                <div className="text-3xl font-black text-[#D4A017]">5</div>
                <div className="text-white/40 text-xs mt-1">отраслей</div>
              </div>
            </div>
          </motion.div>

          {/* Right */}
          <div className="space-y-4">
            {pillars.map((p, i) => (
              <motion.div
                key={p.title}
                initial={{ opacity: 0, x: 40 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ delay: 0.2 + i * 0.15, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                className="group flex gap-5 bg-white/[0.03] border border-white/8 rounded-2xl p-6 hover:border-[#D4A017]/25 hover:bg-white/[0.05] transition-all duration-400"
              >
                <div className="w-12 h-12 bg-[#D4A017]/10 border border-[#D4A017]/20 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 group-hover:bg-[#D4A017]/20 transition-colors">
                  {p.icon}
                </div>
                <div>
                  <h3 className="font-bold mb-2 group-hover:text-[#D4A017] transition-colors">{p.title}</h3>
                  <p className="text-white/50 text-sm leading-relaxed">{p.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
