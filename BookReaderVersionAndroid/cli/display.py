import os
import sys


def clear_screen() -> None:
    if os.environ.get("TERM") or os.name != "nt":
        os.system("clear 2>/dev/null || cls")
    else:
        os.system("cls")


def pause(message: str = "Нажмите Enter...") -> None:
    try:
        input(message)
    except (EOFError, KeyboardInterrupt):
        print()
        raise


def print_header(title: str) -> None:
    width = max(len(title) + 4, 40)
    line = "═" * width
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def print_error(message: str) -> None:
    print(f"\n✗ {message}")


def print_success(message: str) -> None:
    print(f"\n✓ {message}")


def print_section(title: str) -> None:
    print(f"\n  ── {title} ──")


def print_hint(message: str) -> None:
    print(f"  · {message}")


def print_form_step(step: int, total: int, title: str) -> None:
    print(f"\n  Шаг {step} из {total} · {title}")
    print("  " + "─" * 32)


def print_key_value(label: str, value: str, *, empty: str = "—", width: int = 14) -> None:
    display = value.strip() if value and value.strip() else empty
    print(f"  {label:<{width}} {display}")


def print_shortcuts(*shortcuts: tuple[str, str]) -> None:
    parts = [f"[{key}] {label}" for key, label in shortcuts]
    print(f"\n  {'  '.join(parts)}")


def progress_bar(percent: float, width: int = 24) -> str:
    percent = max(0.0, min(100.0, percent))
    filled = round(width * percent / 100)
    return "█" * filled + "░" * (width - filled)


def horizontal_bar(value: float, max_value: float, width: int = 20) -> str:
    if max_value <= 0:
        return "░" * width
    ratio = min(max(value / max_value, 0.0), 1.0)
    filled = round(width * ratio)
    return "█" * filled + "░" * (width - filled)


def ask_int(
    prompt: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
    hint: str | None = None,
) -> int | None:
    if hint:
        print_hint(hint)
    raw = input(f"  {prompt}: ").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        print_error("Введите целое число")
        return None
    if min_value is not None and value < min_value:
        print_error(f"Значение должно быть ≥ {min_value}")
        return None
    if max_value is not None and value > max_value:
        print_error(f"Значение должно быть ≤ {max_value}")
        return None
    return value


def ask_float(prompt: str) -> float | None:
    raw = input(f"{prompt}: ").strip()
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        print_error("Введите число")
        return None


def ask_text(
    prompt: str,
    *,
    required: bool = False,
    hint: str | None = None,
    default: str | None = None,
) -> str | None:
    if hint:
        print_hint(hint)
    suffix = ""
    if default:
        suffix = f" [{default}]"
    raw = input(f"  {prompt}{suffix}: ").strip()
    if not raw and default is not None:
        return default
    if required and not raw:
        print_error("Поле обязательно")
        return None
    return raw


def ask_yes_no(prompt: str, *, default: bool = False) -> bool:
    default_label = "д" if default else "н"
    while True:
        raw = input(f"  {prompt} (д/н, Enter — {default_label}): ").strip().lower()
        if raw == "":
            return default
        if raw in {"д", "y", "yes", "да"}:
            return True
        if raw in {"н", "n", "no", "нет"}:
            return False
        print_error("Введите «д» или «н»")


def choose_from_menu(options: list[str], *, title: str = "Выберите пункт") -> int | None:
    print_header(title)
    for index, label in enumerate(options, start=1):
        print(f"  {index}. {label}")
    print("  0. Назад")

    choice = ask_int("\nПункт", min_value=0, max_value=len(options))
    if choice is None:
        return None
    if choice == 0:
        return 0
    return choice


def ensure_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass
