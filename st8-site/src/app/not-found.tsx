import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <section className="flex flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-gold">404</p>
      <h1 className="mt-4 text-3xl font-semibold tracking-tight">
        Страница не найдена
      </h1>
      <p className="mt-3 max-w-md text-foreground/70">
        Возможно, страница была перемещена или адрес введён с ошибкой.
      </p>
      <Button asChild className="mt-8 bg-gold text-[#0a0a0a] hover:bg-gold/90">
        <Link href="/">На главную</Link>
      </Button>
    </section>
  );
}
