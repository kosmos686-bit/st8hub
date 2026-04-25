"use client";

import { useRef, useState } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";

export default function CTA() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });
  const [form, setForm] = useState({ name: "", company: "", contact: "", message: "" });
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSent(true);
    }, 1200);
  };

  const inputClass =
    "w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm placeholder-white/25 focus:outline-none focus:border-[#D4A017]/50 focus:bg-white/[0.06] transition-all duration-200";

  return (
    <section id="contact" className="py-28 px-6">
      <div className="max-w-2xl mx-auto" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <span className="text-[#D4A017] text-xs font-bold uppercase tracking-[0.2em] mb-5 block">
            Контакт
          </span>
          <h2 className="text-4xl lg:text-5xl font-black mb-4">
            Готовы запустить{" "}
            <span className="text-gradient">AI-продажи?</span>
          </h2>
          <p className="text-white/55 text-lg">
            Расскажите о бизнесе — подберём решение за 24 часа.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="bg-white/[0.03] border border-white/10 rounded-3xl p-8"
          style={{ boxShadow: "0 0 60px rgba(212,160,23,0.05)" }}
        >
          <AnimatePresence mode="wait">
            {sent ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-10"
              >
                <div className="text-6xl mb-5">✅</div>
                <h3 className="text-2xl font-black mb-3">Заявка отправлена!</h3>
                <p className="text-white/55">Свяжемся в течение 24 часов.</p>
              </motion.div>
            ) : (
              <motion.form key="form" onSubmit={handleSubmit} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <input
                    type="text"
                    placeholder="Ваше имя"
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className={inputClass}
                  />
                  <input
                    type="text"
                    placeholder="Компания"
                    required
                    value={form.company}
                    onChange={(e) => setForm({ ...form, company: e.target.value })}
                    className={inputClass}
                  />
                </div>
                <input
                  type="text"
                  placeholder="Telegram или телефон"
                  required
                  value={form.contact}
                  onChange={(e) => setForm({ ...form, contact: e.target.value })}
                  className={inputClass}
                />
                <textarea
                  placeholder="Расскажите о задаче (необязательно)"
                  rows={4}
                  value={form.message}
                  onChange={(e) => setForm({ ...form, message: e.target.value })}
                  className={`${inputClass} resize-none`}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="relative overflow-hidden w-full py-4 bg-[#D4A017] text-[#0A0F1A] font-black rounded-xl hover:bg-[#F5C842] transition-all duration-200 hover:shadow-[0_0_30px_rgba(212,160,23,0.4)] disabled:opacity-70 group"
                >
                  <span className="relative z-10">
                    {loading ? "Отправляем…" : "Отправить заявку"}
                  </span>
                  <span className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </section>
  );
}
