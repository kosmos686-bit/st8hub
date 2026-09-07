import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Политика конфиденциальности",
  description: "Политика обработки персональных данных ST8-AI.",
  robots: { index: false, follow: false },
};

export default function PrivacyPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">
          Политика конфиденциальности
        </h1>

        <div className="mt-6 rounded-xl border border-gold/20 bg-gold/5 p-4 text-sm text-foreground/70">
          Черновик по типовой структуре 152-ФЗ. Реквизиты оператора ниже —
          заглушки, требуют подтверждения. Перед публикацией текст должен
          проверить юрист — это не готовый юридический документ.
        </div>

        <div className="mt-10 space-y-8 text-sm leading-relaxed text-foreground/70">
          <div>
            <h2 className="mb-2 text-base font-semibold text-foreground">
              1. Оператор персональных данных
            </h2>
            <p>
              [Наименование ЮЛ — уточняется], ИНН [уточняется], ОГРН
              [уточняется], юридический адрес: [уточняется] (далее —
              «Оператор»).
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-base font-semibold text-foreground">
              2. Какие данные обрабатываются
            </h2>
            <p>
              Имя, телефон, email, название компании — данные, которые
              пользователь указывает в формах на сайте (заявка, контактная
              форма).
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-base font-semibold text-foreground">
              3. Цели обработки
            </h2>
            <p>
              Обработка заявок, связь с пользователем по вопросам
              сотрудничества, подготовка коммерческого предложения.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-base font-semibold text-foreground">
              4. Права субъекта персональных данных
            </h2>
            <p>
              Вы вправе запросить доступ к своим данным, их уточнение или
              удаление, обратившись по контактам, указанным в футере сайта.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-base font-semibold text-foreground">
              5. Хранение и защита данных
            </h2>
            <p>
              Данные хранятся не дольше, чем это необходимо для целей
              обработки, и защищены от несанкционированного доступа
              организационными и техническими мерами.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-base font-semibold text-foreground">
              6. Контакты
            </h2>
            <p>По вопросам обработки данных — см. раздел «Контакты» в футере.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
