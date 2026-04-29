import os
import errno
import time
import json
import selectors
from enum import StrEnum


class PrismPlayPipe():

    class Status(StrEnum):
        IDLE = "idle"
        RUNNING = "running"
        COMPLETE = "complete"
        ERROR = "error"
        STEP = "step"

    class Result(StrEnum):
        PASS = "PASS"
        FAIL = "FAIL"
        NA = "NA"

    class Cmd(StrEnum):
        PLAY = "play"
        STATUS = "status"
        CANCEL = "cancel"

    class Fields(StrEnum):
        CMD = "cmd"
        CHANNEL = "channel"
        STATUS = "status"
        RESULT = "result"
        MESSAGE = "message"
        ERROR = "error"
        ARTIFACT = "artifact"
        REFERENCES = "references"

    PUBLIC_PATH = "public"

    _PIPE_FN_BASE = "prism_play_pipe_ch"

    def __init__(self, client, channel, logger, work_dir):

        self.client = client
        self.channel = channel
        self.logger = logger
        self.rel_work_path = os.path.join(self.PUBLIC_PATH, work_dir)
        self.abs_work_path = self._determine_abs_work_path(work_dir)

        cmd_pipe_path = os.path.join(
            self.abs_work_path, f"{self._PIPE_FN_BASE}{self.channel}-cmd.pipe"
        )
        stat_pipe_path = os.path.join(
            self.abs_work_path, f"{self._PIPE_FN_BASE}{self.channel}-stat.pipe"
        )
        self.logger.info(
            f"Initializing PrismPlayPipe: client={self.client}, channel={self.channel}, "
            f"cmd_pipe={cmd_pipe_path}, stat_pipe={stat_pipe_path}"
        )
        if self.client:
            self.pipe_write_path = cmd_pipe_path
            self.pipe_read_path = stat_pipe_path
        else:
            self.pipe_write_path = stat_pipe_path
            self.pipe_read_path = cmd_pipe_path
        self.pipe_read = None
        self.pipe_sel = None

        self.logger.info(f"Initialized PrismPlayPipe: channel={self.channel}")

    def _determine_abs_work_path(self, work_dir):

        # Use public/actions-runner as base path for pipes; determine it relative to the location
        # of this file to handle host OS and docker scenarios
        _file_path = os.path.dirname(os.path.abspath(__file__))
        _index = _file_path.find(self.PUBLIC_PATH)
        if _index == -1:
            self.logger.error(
                f"Could not find {self.PUBLIC_PATH} in file path {_file_path}"
            )
            raise Exception(f"Could not find {self.PUBLIC_PATH} in file path {_file_path}")

        _abs_work_path = os.path.join(
            _file_path[: _index + len(self.PUBLIC_PATH)],
            work_dir
        )

        if not os.path.isdir(_abs_work_path):
            self.logger.error(
                f"Directory {work_dir} not in expected location {_abs_work_path}"
            )
            raise Exception(
                f"Directory {work_dir} not in expected location {_abs_work_path}"
            )

        return _abs_work_path

    def create(self):

        for pipe_path in [self.pipe_write_path, self.pipe_read_path]:
            self.logger.info(f"Creating named pipe {pipe_path}")

            try:
                os.mkfifo(pipe_path, 0o666)
                os.chmod(pipe_path, 0o666)  # Update permissions ignoring umask

            except FileExistsError:
                pass
            except OSError as e:
                self.logger.error(f"Creating pipe {pipe_path}: {e}")
                raise

    def open(self):

        # Ensure Pipes exist before opening
        if not os.path.exists(self.pipe_write_path) or not os.path.exists(self.pipe_read_path):
            self.create()

        try:

            self.logger.info(f"Opening Read Pipe: {self.pipe_read_path}")

            self.pipe_read = os.fdopen(
                os.open(self.pipe_read_path, flags=os.O_NONBLOCK | os.O_RDONLY), "r"
            )
            self.pipe_sel = selectors.DefaultSelector()
            self.pipe_sel.register(self.pipe_read, selectors.EVENT_READ)
        except OSError as e:
            self.logger.error(f"Error: {e}")
            raise

    def close(self):
        try:
            if self.pipe_sel:
                self.pipe_sel.close()
            if self.pipe_read:
                self.pipe_read.close()
        except Exception as e:
            self.logger.error(f"Error: {e}")

    def read(self, timeout=None) -> dict | None:

        ts_start = time.time()
        done_once = False

        self.logger.debug("Waiting for read...")
        while (timeout == 0 and not done_once or
               timeout is None or
               timeout > 0 and time.time() - ts_start < timeout):
            try:
                done_once = True
                for key, __ in self.pipe_sel.select(timeout=0.1):
                    data = key.fileobj.readline()
                    if not data:
                        continue
                    try:
                        msg = json.loads(data)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON decode error: {e} for data: {data}")
                        raise
                    self.logger.debug(f"Read from pipe: {msg}")
                    return msg
            except Exception as e:
                self.logger.error(f"Exception: {e}", exc_info=True)
                raise

        self.logger.debug("No data read")
        return None

    def write(self, msg):
        try:
            self.logger.debug(f"Writing to pipe: {msg}")
            with os.fdopen(
                os.open(self.pipe_write_path, flags=os.O_NONBLOCK | os.O_WRONLY), 'w'
            ) as pipe_write:
                data = json.dumps(msg)
                pipe_write.write(data)
            return True
        except OSError as e:
            if e.errno == errno.ENXIO:
                self.logger.error("No one is listening :(")
            else:
                self.logger.error(f"OSError: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Exception: {e}", exc_info=True)

        return False
