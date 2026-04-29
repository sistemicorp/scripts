#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023-2026
Martin Guthrie
"""

import os
import sys
import time
import logging
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from prism_play_pipe import PrismPlayPipe
except ImportError:
    # Fallback if run from different location
    from public.prism.drivers.prism_play.prism_play_pipe import PrismPlayPipe


def parse_args():
    epilog = """
    Usage examples:
       python3 prism_play_cli.py play -c 0 -a my-artifact -r "ref1,ref2"

    Commands:
        play   Trigger play on a channel
    """
    parser = argparse.ArgumentParser(
        description='Prism Play Pipe CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )

    parser.add_argument(
        "-c", "--channel", type=int, required=True, help="Channel number"
    )
    parser.add_argument(
        "-w", "--work_dir", type=str, required=True, help="Working directory"
    )
    parser.add_argument(
        "-t", "--timeout", type=int, default=300, help="Timeout in seconds"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        default=0,
        action="count",
        help="Increase verbosity",
    )

    subp = parser.add_subparsers(title="commands", dest="_cmd", help='commands')

    # play command
    play_parser = subp.add_parser("play", help="Play channel")
    play_parser.add_argument(
        "-a", "--artifact", type=str, default=None, help="Artifact path"
    )
    play_parser.add_argument(
        "-r", "--references", type=str, default=None, help="References (comma-separated)"
    )

    args = parser.parse_args()
    return args


def _get_pipe(channel, work_dir, logger):
    """Helper to create and open a PrismPlayPipe for the given channel.

    returns: Opened PrismPlayPipe instance
    """

    pipe = PrismPlayPipe(client=True, channel=channel, logger=logger, work_dir=work_dir)
    pipe.open()
    return pipe


def cmd_play(args, pipe):
    """Send play command to Prism and wait for completion, error or timeout.

    returns: True if passed, False if failed, None if error or timeout
    """

    msg = {
        PrismPlayPipe.Fields.CMD: PrismPlayPipe.Cmd.PLAY,
        PrismPlayPipe.Fields.CHANNEL: args.channel,
        PrismPlayPipe.Fields.ARTIFACT: args.artifact,
        PrismPlayPipe.Fields.REFERENCES: args.references.split(",") if args.references else None
    }

    logger.info(f"Sending play command: {msg}")

    if not pipe.write(msg):
        return False

    # Read response until COMPLETE status, error or timeout
    ts_start = time.time()

    while time.time() - ts_start < (args.timeout):
        response = pipe.read(timeout=1)
        if not response:
            continue

        if response.get(PrismPlayPipe.Fields.STATUS) == PrismPlayPipe.Status.COMPLETE:
            logger.info(f"Play completed with result: {response.get(PrismPlayPipe.Fields.RESULT)}")
            if response.get(PrismPlayPipe.Fields.RESULT) == PrismPlayPipe.Result.PASS:
                return True
            elif response.get(PrismPlayPipe.Fields.RESULT) == PrismPlayPipe.Result.FAIL:
                return False
            else:
                logger.error(f"Unexpected result: {response.get(PrismPlayPipe.Fields.RESULT)}")
                return None
        elif response.get(PrismPlayPipe.Fields.STATUS) == PrismPlayPipe.Status.ERROR:
            logger.error(
                f"Play returned error: {response.get(PrismPlayPipe.Fields.ERROR, 'Unknown error')}"
            )
            return None
        elif response.get(PrismPlayPipe.Fields.STATUS) == PrismPlayPipe.Status.IDLE:
            logger.info("Prism is idle")
        elif response.get(PrismPlayPipe.Fields.STATUS) == PrismPlayPipe.Status.STEP:
            logger.info(f"Step update: {response.get(PrismPlayPipe.Fields.MESSAGE, 'NA')}")

    logger.error(f"Play command timed out after {args.timeout}s")
    return None

if __name__ == '__main__':
    args = parse_args()
    exit_code = -1
    success = None
    # Setup logging
    if args.verbose == 0:
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)6s %(message)s'
        )
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s'
        )

    logger = logging.getLogger(__name__)

    pipe = _get_pipe(args.channel, args.work_dir, logger)

    if args._cmd is None:
        logger.error("No command specified. Use -h for help.")
    elif args._cmd == 'play':
        success = cmd_play(args, pipe)
    else:
        logger.error(f"Unknown command: {args._cmd}")

    if success is True:
        logger.info("Passed")
        exit_code = 0
    elif success is False:
        logger.error("Failed")
        exit_code = 1
    else:
        logger.error("Unexpected result")
        exit_code = -1

    exit(exit_code)
