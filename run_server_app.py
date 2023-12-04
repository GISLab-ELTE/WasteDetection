import logging
import argparse

from model.model import Model
from model.persistence import Persistence
from server_app.src.process import Process


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: Parsed arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--download-update",
        action="store_true",
        default=False,
        help="Download new images.",
    )

    parser.add_argument(
        "-i",
        "--download-init",
        action="store_true",
        default=False,
        help="Initialize image database: Download all the images on the given time interval.",
    )

    parser.add_argument(
        "-cl",
        "--classify",
        action="store_true",
        default=False,
        help="Execute classification (does not download images).",
    )

    parsed_args = parser.parse_args()

    return parsed_args


def setup_logging() -> None:
    """
    Configures logging style.

    """

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    args = parse_args()

    setup_logging()

    print("AUTOMATIC WASTE DETECTION")

    CONFIG_FILE_NAME_DESKTOP_APP = "server_app/resources/config.sample.json"

    model = Model(
        Persistence(config_file_path=CONFIG_FILE_NAME_DESKTOP_APP)
    )

    process = Process(model, args.download_init, args.download_update, args.classify)
    process.mainloop()
