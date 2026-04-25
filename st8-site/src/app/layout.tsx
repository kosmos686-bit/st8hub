import type { Metadata } from "next";
import { Montserrat } from "next/font/google";
import "./globals.css";

const montserrat = Montserrat({
  subsets: ["latin", "cyrillic"],
  variable: "--font-montserrat",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ST8-AI — Интеллектуальные продажи",
  description: "AI-решения для B2B продаж в России. Автоматизируем лидогенерацию, квалификацию и закрытие сделок.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className={`${montserrat.variable} font-montserrat antialiased`}>
        {children}
      </body>
    </html>
  );
}
