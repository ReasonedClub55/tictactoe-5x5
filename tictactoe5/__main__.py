"""Entry point: ``python -m tictactoe5``."""

import sys

from . import cli


def main() -> int:
    """Run the game, treating Ctrl-C/EOF as a normal exit."""
    try:
        return cli.run()
    except (KeyboardInterrupt, EOFError):
        return 0


if __name__ == "__main__":
    sys.exit(main())
