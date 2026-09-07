"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

const SESSION_KEY = "st8-preloader-shown";
const DURATION_MS = 1600;

export function Preloader({ onComplete }: { onComplete: () => void }) {
  const [skip, setSkip] = useState(true);
  const [visible, setVisible] = useState(true);
  const [progress, setProgress] = useState(0);

  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    const alreadyShown = sessionStorage.getItem(SESSION_KEY);

    if (alreadyShown || reduceMotion) {
      onCompleteRef.current();
      return;
    }

    setSkip(false);

    const start = performance.now();
    let raf: number;

    const tick = (now: number) => {
      const elapsed = now - start;
      const pct = Math.min(100, Math.round((elapsed / DURATION_MS) * 100));
      setProgress(pct);
      if (pct < 100) {
        raf = requestAnimationFrame(tick);
      } else {
        // Marked as shown only once the run actually finishes — writing it
        // at start would make React Strict Mode's dev-only double-invoke of
        // this effect see the flag as already set on its second (kept) run
        // and bail out before the counter ever starts.
        sessionStorage.setItem(SESSION_KEY, "1");
        setTimeout(() => setVisible(false), 200);
      }
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // Runs once on mount only — onComplete is read via ref to avoid
    // restarting the counter when the parent passes a new inline callback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (skip) return null;

  return (
    <AnimatePresence onExitComplete={() => onCompleteRef.current()}>
      {visible && (
        <motion.div
          exit={{ y: "-100%" }}
          transition={{ duration: 0.7, ease: [0.76, 0, 0.24, 1] }}
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 bg-[#0a0a0a]"
        >
          <div className="text-[clamp(3rem,9vw,5.5rem)] font-semibold tabular-nums tracking-tight text-gold">
            {progress}%
          </div>
          <div className="h-px w-40 overflow-hidden bg-white/10">
            <div
              className="h-full bg-gold transition-[width] duration-75 ease-linear"
              style={{ width: `${progress}%` }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
