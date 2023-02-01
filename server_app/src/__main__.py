import argparse

from process import Process


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: parsed arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-st",
        "--startup",
        action='store_true',
        default=False,
        help="Run startup process or not.",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        action='store_true',
        default=False,
        help="Sleep after execution or not.",
    )

    parsed_args = parser.parse_args()

    return parsed_args


if __name__ == "__main__":
    args = parse_args()

    print("Automatic waste detection")

    process = Process()
    process.mainloop(args.startup, args.sleep)
