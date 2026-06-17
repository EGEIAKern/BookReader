#!/data/data/com.termux/files/usr/bin/bash
# Установка Book Tracker в Termux
set -e

echo "==> Обновление пакетов Termux..."
pkg update -y
pkg install -y python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Проверка Python..."
python3 --version

echo ""
echo "Готово! Запуск:"
echo "  cd \"$SCRIPT_DIR\""
echo "  python3 main.py"
echo ""
echo "Опционально (экспорт Excel):"
echo "  pip install openpyxl"
echo ""
echo "Данные сохраняются в ~/.book-tracker/data/"
echo ""
echo "Облачная синхронизация (ПК + телефон):"
echo "  python3 main.py → пункт «4. Облако»"
echo "  Поддерживаются папка облака и WebDAV (Яндекс.Диск, Nextcloud)"
