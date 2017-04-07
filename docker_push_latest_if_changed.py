#!/usr/bin/env python3
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--source', required=True,
        help=(
            'Local image tag to be considered for pushing.  '
            'For example `--source docker.example.com/img-name:2017.01.05`.'
        ),
    )
    parser.add_argument(
        '--target',
        help=(
            'Target remote image to push if the docker image is changed.  '
            'If omitted, the image will be $repository:latest of the '
            '`--source` image.'
        ),
    )
    parser.parse_args(argv)


if __name__ == '__main__':
    exit(main())
