#!/usr/bin/env python3
"""Extract source material for deterministic learning-page generation."""

import os
import sys


def configure_output_dir(argv):
    """Set the output directory before importing extractor.config."""
    for index, value in enumerate(argv):
        if value == "--output-dir" and index + 1 < len(argv):
            os.environ["LEARNING_SKILL_WORKDIR"] = os.path.abspath(argv[index + 1])
            return


configure_output_dir(sys.argv[1:])

# Ensure the scripts/ directory (where the 'extractor' package lives) is in sys.path
# so the modular package can be imported reliably regardless of the working directory.
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))

from extractor.utils import main

if __name__ == "__main__":
    main()
