import sys


def prompt_for_input():
    v = input("\n\n ** apply: [y/N] ")

    if v not in ["y", "Y"]:
        print(f"received '{v}', expecting 'y' or 'Y' - exiting")
        sys.exit(0)
    else:
        print("proceeding")
