import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Согласие на обработку персональных данных",
  description: "Согласие на обработку персональных данных ST8-AI.",
  robots: { index: false, follow: false },
};

export default function ConsentPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">
          Согласие на обработку персональных данных
        </h1>

        <div className="mt-6 rounded-xl border border-gold/20 bg-gold/5 p-4 text-sm text-foreground/70">
          Черновик по типовой структуре 152-ФЗ. Реквизиты оператора ниже —
          заглушки, требуют подтверждения. Перед публикацией текст должен
          проверить юрист — это не готовый юридический документ.
        </div>

        <div className="mt-10 space-y-6 text-sm leading-relaxed text-foreground/70">
          <p>
            Заполняя форму на сайте st8-ai.ru, я даю согласие [Наименование
            ЮЛ — уточняется], ИНН [уточняется] (далее — «Оператор»), на
            обработку моих персональных данных (имя, телефон, email,
            название компании) в целях обработки заявки и связи со мной по
            вопросам сотрудничества.
          </p>
          <p>
            Согласие действует до момента его отзыва. Отозвать согласие
            можно, обратившись по контактам, указанным в футере сайта.
          </p>
          <p>
            Обработка осуществляется в соответствии с Федеральным законом
            №152-ФЗ «О персональных данных» и Политикой конфиденциальности
            Оператора.
          </p>
        </div>
      </div>
    </section>
  );
}
