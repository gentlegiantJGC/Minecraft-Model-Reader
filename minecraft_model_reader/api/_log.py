import logging
import sys

"""
By default the logger only logs to the console.
If you wish to modify the handlers you should
1) Get the logger
2) Remove and close all existing handlers
3) Set up the logger how you desire

Step 2 may not be required if you set up the logger before this module is imported
but there is no harm in doing it and if you don't everything may get logged to the console twice.
"""


main_log = logging.getLogger("minecraft_model_reader")
if not main_log.handlers:
    main_log.setLevel(logging.DEBUG if "amulet-debug" in sys.argv else logging.INFO)

    formatter = logging.Formatter("%(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    main_log.addHandler(console_handler)
