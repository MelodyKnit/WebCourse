import logging

FORMAT = ("\033[1;35m%(asctime)s\033[0m "
          "\033[1;33m[%(levelname)s]\033[0m "
          "%(funcName)s | %(message)s")
logging.basicConfig(format=FORMAT, level=0)

logger = logging
