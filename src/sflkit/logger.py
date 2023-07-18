import logging

LOGGER = logging.getLogger("sflkit")
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s :: %(levelname)-8s :: %(message)s",
)
