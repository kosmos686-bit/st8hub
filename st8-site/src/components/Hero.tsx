"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";

interface CountUpProps {
  target: number;
  suffix: string;
  duration?: number;
}

function CountUp({ target, suffix, duration = 2000 }: CountUpProps) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const isFloat = !Number.isInteger(target);

  useEffect(() => {
    if (!inView) return;
    const start = performance.now();
    const step = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      const val = eased * target;
      setCount(isFloat ? Math.round(val * 10) / 10 : Math.floor(val));
      if (p < 1) requestAnimationFrame(step);
      else setCount(target);
    };
    requestAnimationFrame(step);
  }, [inView, target, duration, isFloat]);

  return (
    <span ref={ref}>
      {isFloat ? count.toFixed(1) : count}
      {suffix}
    </span>
  );
}

function DashboardMockup() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50, rotateY: -15 }}
      animate={{ opacity: 1, y: 0, rotateY: 0 }}
      transition={{ delay: 0.9, duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
      style={{ perspective: "1200px" }}
      className="relative"
    >
      <motion.div
        animate={{ y: [0, -14, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        className="relative bg-[#0D1828]/90 border border-[#D4A017]/25 rounded-2xl p-6 backdrop-blur-sm"
        style={{
          boxShadow:
            "0 0 0 1px rgba(212,160,23,0.1), 0 0 60px rgba(212,160,23,0.12), 0 40px 80px rgba(0,0,0,0.7)",
        }}
      >
        {/* Window bar */}
        <div className="flex items-center gap-2 mb-5">
          <div className="w-3 h-3 rounded-full bg-[#FF5F57]/80" />
          <div className="w-3 h-3 rounded-full bg-[#FEBC2E]/80" />
          <div className="w-3 h-3 rounded-full bg-[#28C840]/80" />
          <div className="ml-auto flex items-center gap-1.5 bg-white/5 rounded-md px-3 py-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[#D4A017] animate-pulse" />
            <span className="text-[10px] text-white/40 font-mono">ST8 AI Hub</span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          {[
            { label: "Клиентов", value: "47", delta: "+3" },
            { label: "Выручка", value: "5.8М", delta: "+200к" },
            { label: "Конверсия", value: "94%", delta: "+7%" },
          ].map((s) => (
            <div key={s.label} className="bg-[#0A0F1A]/70 rounded-xl p-3">
              <div className="text-[#D4A017] font-bold text-lg leading-none">{s.value}</div>
              <div className="text-white/40 text-[10px] mt-1">{s.label}</div>
              <div className="text-green-400/70 text-[9px] mt-1">{s.delta}</div>
            </div>
          ))}
        </div>

        {/* Bar chart */}
        <div className="flex items-end gap-1.5 h-16 mb-5">
          {[35, 55, 42, 70, 60, 85, 65, 90, 75, 100, 82, 95].map((h, i) => (
            <motion.div
              key={i}
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ delay: 1.4 + i * 0.04, duration: 0.35 }}
              className="flex-1 rounded-sm origin-bottom"
              style={{ height: `${h}%`, background: "rgba(212,160,23,0.15)" }}
            >
              <motion.div
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ delay: 1.5 + i * 0.04, duration: 0.3 }}
                className="w-full rounded-sm origin-bottom"
                style={{ height: "35%", background: "#D4A017" }}
              />
            </motion.div>
          ))}
        </div>

        {/* Pipeline */}
        <div className="space-y-2">
          {[
            { name: "AIRI", status: "Договор", color: "text-green-400" },
            { name: "Большакова Ю.", status: "Подписание", color: "text-[#D4A017]" },
            { name: "Unik Food", status: "Тест", color: "text-blue-400" },
          ].map((c, i) => (
            <motion.div
              key={c.name}
              initial={{ opacity: 0, x: -15 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.8 + i * 0.1 }}
              className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0"
            >
              <span className="text-white/60 text-xs">{c.name}</span>
              <span className={`text-xs font-semibold ${c.color}`}>{c.status}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Ambient glow */}
      <div className="absolute inset-0 -z-10 blur-3xl opacity-15 bg-[#D4A017] rounded-full scale-[0.7]" />
    </motion.div>
  );
}

const words = "Интеллектуальные продажи для вашего бизнеса".split(" ");

const metrics = [
  { value: 47, suffix: "+", label: "клиентов" },
  { value: 94, suffix: "%", label: "конверсия" },
  { value: 5.8, suffix: "М ₽", label: "выручка партнёров" },
];

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-[#0A0F1A]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_50%,rgba(212,160,23,0.06)_0%,transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_80%_20%,rgba(212,160,23,0.04)_0%,transparent_50%)]" />

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(212,160,23,0.5) 1px,transparent 1px),linear-gradient(90deg,rgba(212,160,23,0.5) 1px,transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />

      <div className="relative max-w-7xl mx-auto px-6 pt-28 pb-20 grid lg:grid-cols-2 gap-16 items-center w-full">
        {/* Left — text */}
        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#D4A017]/10 border border-[#D4A017]/25 rounded-full text-[#D4A017] text-xs font-semibold tracking-wide mb-8"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4A017] animate-pulse" />
            AI-решения для бизнеса
          </motion.div>

          <h1 className="text-4xl lg:text-[3.25rem] font-black leading-[1.1] mb-6">
            {words.map((word, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 + i * 0.07, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                className="inline-block mr-3"
              >
                {i < 2 ? <span className="text-gradient">{word}</span> : word}
              </motion.span>
            ))}
          </h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9, duration: 0.6 }}
            className="text-white/55 text-lg leading-relaxed mb-10 max-w-lg"
          >
            Автоматизируем B2B продажи с помощью AI-агентов.
            Больше лидов, быстрее сделки, предсказуемый результат.
          </motion.p>

          {/* Metrics */}
          <div className="flex gap-8 mb-10">
            {metrics.map((m, i) => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.1 + i * 0.1 }}
              >
                <div className="text-2xl font-black text-[#D4A017]">
                  <CountUp target={m.value} suffix={m.suffix} />
                </div>
                <div className="text-white/40 text-xs mt-1">{m.label}</div>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="flex flex-wrap gap-4"
          >
            <a
              href="#contact"
              className="relative overflow-hidden px-8 py-3.5 bg-[#D4A017] text-[#0A0F1A] font-bold rounded-full hover:bg-[#F5C842] transition-all duration-200 hover:shadow-[0_0_30px_rgba(212,160,23,0.5)] group"
            >
              <span className="relative z-10">Начать проект</span>
              <span className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/25 to-transparent" />
            </a>
            <a
              href="#cases"
              className="px-8 py-3.5 border border-white/15 text-white/70 rounded-full hover:border-[#D4A017]/50 hover:text-[#D4A017] transition-all duration-200"
            >
              Смотреть кейсы
            </a>
          </motion.div>
        </div>

        {/* Right — dashboard */}
        <div className="hidden lg:flex justify-center">
          <div className="w-full max-w-md">
            <DashboardMockup />
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          className="w-px h-14 bg-gradient-to-b from-[#D4A017]/50 to-transparent"
        />
        <span className="text-white/20 text-[10px] tracking-[0.2em] uppercase">scroll</span>
      </motion.div>
    </section>
  );
}
