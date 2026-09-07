import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { MotionConfig } from "motion/react";
import "./globals.css";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { CookieBanner } from "@/components/cookie-banner";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "cyrillic"],
});

const siteUrl = "https://st8-ai.ru";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "ST8-AI — AI-автоматизация для бизнеса",
    template: "%s | ST8-AI",
  },
  description:
    "ST8-AI внедряет AI-автоматизацию для HoReCa, производства, ритейла, логистики и офисов: от чат-ботов до полной интеграции с вашими системами.",
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: "ST8-AI",
    url: siteUrl,
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ru" className={`dark ${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: "ST8-AI",
              url: siteUrl,
              description:
                "AI-автоматизация для бизнеса: HoReCa, производство, ритейл, логистика, офисы.",
            }),
          }}
        />
        <MotionConfig reducedMotion="user">
          <Header />
          <main className="flex-1 pt-16 sm:pt-[72px]">{children}</main>
          <Footer />
          <CookieBanner />
        </MotionConfig>
      </body>
    </html>
  );
}
