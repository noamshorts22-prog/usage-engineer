#!/usr/bin/env python3
"""Run usage-engineer from a source checkout without installing it: python ue.py <command>."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from usage_engineer.ue import main  # noqa: E402

sys.exit(main())
