import logging
import argparse

from process import Process


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: Parsed arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-st",
        "--startup",
        action="store_true",
        default=False,
        help="Run startup process or not.",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        action="store_true",
        default=False,
        help="Sleep after execution or not.",
    )
    parser.add_argument(
        "-cl",
        "--classify",
        action="store_true",
        default=False,
        help="Do classification instead of downloading images."
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

    process = Process(args.classify)
    process.mainloop(args.startup, args.sleep)
