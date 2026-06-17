#!/usr/bin/env python3
"""Book Tracker — консольная версия для Termux (Android)."""

from cli.app import BookTrackerApp


def main() -> None:
    BookTrackerApp().run()


if __name__ == "__main__":
    main()
