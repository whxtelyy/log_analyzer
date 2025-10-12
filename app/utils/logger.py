import logging
import os


def setup_logger():
    log_dir = "app/logs"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
        filename=os.path.join(log_dir, "app.log"),
        encoding="utf-8",
        filemode="a",
        force=True,
    )
