"""ST8-AI Панель управления сервисами — запускать через START.bat"""
import os, sys, time, msvcrt
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from service_manager import get_all_status, start_service, stop_service, SERVICES

G = '\033[92m'   # green
R = '\033[91m'   # red
Y = '\033[93m'   # yellow
C = '\033[96m'   # cyan
W = '\033[97m'   # white
B = '\033[1m'    # bold
X = '\033[0m'    # reset
CL = '\033[2J\033[H'  # clear screen


def enable_ansi():
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7
        )
    except Exception:
        pass


def draw(status):
    keys = list(SERVICES.keys())
    print(CL, end='')
    now = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
    print(f"{C}{B}")
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║          ST8-AI  ПАНЕЛЬ УПРАВЛЕНИЯ            ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print(f"{X}  Обновлено: {Y}{now}{X}\n")

    for i, key in enumerate(keys, 1):
        st = status.get(key, {})
        name = SERVICES[key]['name']
        if st.get('running'):
            pid = st.get('pid', '?')
            mem = st.get('mem_mb', 0)
            badge = f"{G}✅ работает{X}"
            detail = f"  PID {pid}  {mem} MB"
        else:
            badge = f"{R}🔴 остановлен{X}"
            detail = ""
        print(f"  {W}[{i}]{X}  {B}{name:<22}{X}  {badge}{detail}")

    print(f"\n  {W}[5]{X}  Запустить ВСЕ")
    print(f"  {W}[6]{X}  Остановить ВСЕ")
    print(f"  {W}[r]{X}  Обновить")
    print(f"  {W}[q]{X}  Выход\n")
    print(f"  Нажмите кнопку: ", end='', flush=True)


def wait_key(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if msvcrt.kbhit():
            ch = msvcrt.getche()
            try:
                return ch.decode('utf-8', errors='replace').lower()
            except Exception:
                return ''
        time.sleep(0.1)
    return ''


def run():
    enable_ansi()
    keys = list(SERVICES.keys())

    while True:
        status = get_all_status()
        draw(status)
        choice = wait_key(30)
        print()

        if choice == 'q':
            print(f"\n{Y}Выход.{X}\n")
            break
        elif choice == 'r' or not choice:
            continue
        elif choice == '5':
            print(f"\n{C}Запуск всех сервисов...{X}")
            for key in keys:
                ok, msg = start_service(key)
                print(f"  {'✅' if ok else '❌'} {SERVICES[key]['name']}: {msg}")
            time.sleep(2)
        elif choice == '6':
            print(f"\n{Y}Остановка всех сервисов...{X}")
            for key in keys:
                ok, msg = stop_service(key)
                print(f"  {'✅' if ok else '⚠️'} {SERVICES[key]['name']}: {msg}")
            time.sleep(2)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                key = keys[idx]
                st = status.get(key, {})
                name = SERVICES[key]['name']
                if st.get('running'):
                    print(f"\n{Y}Останавливаем {name}...{X}")
                    ok, msg = stop_service(key)
                    print(f"  {'✅' if ok else '❌'} {msg}")
                else:
                    print(f"\n{C}Запускаем {name}...{X}")
                    ok, msg = start_service(key)
                    print(f"  {'✅' if ok else '❌'} {msg}")
                time.sleep(2)


if __name__ == '__main__':
    run()
