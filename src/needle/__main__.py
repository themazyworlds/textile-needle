"""
needle main entrypoint.
Supports:
  python -m needle manifest <path>
  python -m needle <path>
"""

import sys

from needle.manifest import main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "manifest":
        sys.argv.pop(1)
    main()
