export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="py-10 px-6 border-t border-white/[0.06]">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <span className="text-xl font-black">
            <span className="text-gradient">ST8</span>
            <span className="text-white/35 text-xs ml-1 font-semibold tracking-widest">AI</span>
          </span>
          <p className="text-white/30 text-xs mt-1">Интеллектуальные продажи для бизнеса</p>
        </div>

        <div className="flex gap-8 text-xs text-white/35">
          <a href="#about" className="hover:text-[#D4A017] transition-colors">О нас</a>
          <a href="#industries" className="hover:text-[#D4A017] transition-colors">Отрасли</a>
          <a href="#cases" className="hover:text-[#D4A017] transition-colors">Кейсы</a>
          <a href="#team" className="hover:text-[#D4A017] transition-colors">Команда</a>
          <a href="#contact" className="hover:text-[#D4A017] transition-colors">Контакт</a>
        </div>

        <p className="text-white/25 text-xs">© {year} ST8-AI</p>
      </div>
    </footer>
  );
}
