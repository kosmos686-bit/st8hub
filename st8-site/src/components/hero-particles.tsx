"use client";

import { useEffect, useState } from "react";

interface Particle {
  id: number;
  left: number;
  top: number;
  delay: number;
  duration: number;
}

export function HeroParticles() {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    setParticles(
      Array.from({ length: 20 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        top: Math.random() * 100,
        delay: Math.random() * 15,
        duration: 10 + Math.random() * 10,
      }))
    );
  }, []);

  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 z-[2] hidden overflow-hidden motion-safe:sm:block"
    >
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute h-0.5 w-0.5 rounded-full bg-gold/40"
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
            animation: `hero-particle-float ${p.duration}s ease-in-out ${p.delay}s infinite`,
          }}
        />
      ))}
    </div>
  );
}
