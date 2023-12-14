import sys
from loguru import logger

""" Complete guide to Loguru:
    https://betterstack.com/community/guides/logging/loguru/
"""
def set_log_level(level="INFO"):
    if not hasattr(set_log_level, "handler_id"):
        set_log_level.handler_id = 0  # it doesn't exist yet, so initialize it
    logger.remove(set_log_level.handler_id)
    set_log_level.handler_id = logger.add(sys.stderr, level=level)

# Set default logger level to INFO
set_log_level("INFO")