import sys


def prompt_for_input():
    v = input("\n\n ** apply: [y/N] ")

    if v not in ["y", "Y"]:
        raise Exception(f"received '{v}', expecting 'y' or 'Y' - exiting")
