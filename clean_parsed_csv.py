"""
Cleaning parsed/saved csv files from invisible space separators and format characters and replacing them with whitespace
"""

import logging

from src import util

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    args = util.parse_args()
    logger.info(f"Reading in file {args.file} and saving as {args.output_file}...")
    util.ParsedContent(args.file).load().clean_content().to_csv(args.output_file)
    logger.info(f"File cleaning complete.")
