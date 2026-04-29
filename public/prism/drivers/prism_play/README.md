# PrismPlay Driver for Command Line Integration

## Overview
* PrismPlay driver allows the Prism driver 'play' feature to be triggered from the command line
  * This allows integration with external processes
* PrismPlay supports passing of a limited number of arguments
  * artifact:  Path to artifact to use for test run
  * references: Comma separated list of reference values.  User determined
* Steps (Where hosted)
  * prism_play_cli.py (Host OS or Prism Docker) --> Named Pipe (Shared Filesystem) --> PrismPlay Prism Driver (Prism Docker) --> Script (Prism Docker)
* Named pipes are used to communicate from prism_play_cli.py (ie command line) to Prism PrismPlay
driver
  * Named pipe file objects are automatically created. For reference only:
    * public/<work-dir>/prism_play_pipe_ch?-cmd.pipe
    * public/<work-dir>/prism_play_pipe_ch?-stat.pipe

## prism_play_cli.py
* Command line application to trigger Prism script to 'Play'
* Must be called from the 'public' hierarchy which contains the Prism script to run
  * File objects (pipes and artifacts) are located relative to the 'public' directory
* Arguments:
  * 'work_dir'/'-w': (Mandatory) Directory where file objects will exist.  Directory must exist immediately
  under 'public' directory.  Must match value provided to PrismPlayer driver.
  * 'channel'/'-c': (Mandatory) Indicates Prism channel to play. 0 based
  * 'cmd' (positional): (Mandatory) Command to run.  Currently only 'play'
  * 'timeout'/'-t': (Default 300) Time in seconds to wait for Prism play to complete
* Prism script with PrismPlay driver installed must be configured and started prior to running
prism_play_cli.py
  * Error message:
    > ERROR No one is listening :(
* Command line documentation:
```
...scripts/public$ ./prism/drivers/prism_play/prism_play_cli.py --help
usage: prism_play_cli.py [-h] -c CHANNEL -w WORK_DIR [-t TIMEOUT] [-v] {play} ...

Prism Play Pipe CLI

options:
  -h, --help            show this help message and exit
  -c CHANNEL, --channel CHANNEL
                        Channel number
  -w WORK_DIR, --work_dir WORK_DIR
                        Working directory
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout in seconds
  -v, --verbose         Increase verbosity

commands:
  {play}                commands
    play                Play channel

    Usage examples:
       python3 prism_play_cli.py play -c 0 -a my-artifact -r "ref1,ref2"

    Commands:
        play   Trigger play on a channel
```
* Example usage for testing:
```
scripts/public$ mkdir actions-runner
scripts/public$ echo "TEST FILE 123" > actions-runner/testfile.txt
scripts/public$ prism/drivers/prism_play/prism_play_cli.py -c 0 -w actions-runner play -r 1234567 -a public/actions-runner/testfile.txt
  INFO Initializing PrismPlayPipe: client=True, channel=0, cmd_pipe=/home/andrew/git/scripts/public/actions-runner/prism_play_pipe_ch0-cmd.pipe, stat_pipe=/home/andrew/git/scripts/public/actions-runner/prism_play_pipe_ch0-stat.pipe
  INFO Initialized PrismPlayPipe: channel=0
  INFO Opening Read Pipe: /home/andrew/git/scripts/public/actions-runner/prism_play_pipe_ch0-stat.pipe
  INFO Sending play command: {<Fields.CMD: 'cmd'>: <Cmd.PLAY: 'play'>, <Fields.CHANNEL: 'channel'>: 0, <Fields.ARTIFACT: 'artifact'>: 'public/actions-runner/testfile.txt', <Fields.REFERENCES: 'references'>: ['1234567']}
  INFO Step update: 0, TST0xxTEARDOWN, UNKNOWN, STATE_DONE, 100%, 4, 4
  INFO Prism is idle
  INFO Step update: 0, TST0xxSETUP, UNKNOWN, STATE_READY, 0%, 1, 4
  INFO Step update: 0, TST0xxSETUP, UNKNOWN, STATE_RUNNING, 25%, 1, 4
  INFO Step update: 0, TST0xxSETUP, PASS, STATE_RUNNING, 25%, 1, 4
  INFO Step update: 0, TST0xxSETUP, PASS, STATE_RUNNING, 25%, 1, 4
  INFO Step update: 0, TST001_KeyAdd, PASS, STATE_RUNNING, 50%, 2, 4
  INFO Step update: 0, TST001_KeyAdd, PASS, STATE_RUNNING, 50%, 2, 4
  INFO Step update: 0, TST001_KeyAdd, PASS, STATE_RUNNING, 50%, 2, 4
  INFO Step update: 0, TST002_UseArtifact, PASS, STATE_RUNNING, 75%, 3, 4
  INFO Step update: 0, TST002_UseArtifact, PASS, STATE_RUNNING, 75%, 3, 4
  INFO Step update: 0, TST002_UseArtifact, PASS, STATE_RUNNING, 75%, 3, 4
  INFO Step update: 0, TST0xxTEARDOWN, PASS, STATE_RUNNING, 75%, 4, 4
  INFO Step update: 0, TST0xxTEARDOWN, PASS, STATE_RUNNING, 75%, 4, 4
  INFO Step update: 0, TST0xxTEARDOWN, PASS, STATE_RUNNING, 75%, 4, 4
  INFO Step update: 0, TST0xxTEARDOWN, PASS, STATE_ENDING, 75%, 4, 4
  INFO Step update: 0, TST0xxTEARDOWN, PASS, STATE_DONE, 75%, 4, 4
  INFO Play completed with result: PASS
  INFO Passed
scripts/public$
```

## Using PrismPlay Driver
* See example script:
  * [public/prism/scripts/example/prod_v0/githubci_0.scr/githubci_0.scr](../../scripts/example/prod_v0/githubci_0.scr)
* PrismPlay Driver must be included in script drivers
  >     "drivers": [["public.prism.drivers.prism_play.hwdrv_prism_play",
  >                     {"work_dir": "actions-runner", "channels": 1}]]
* Script Driver Arguments:
  * 'work_dir': (Mandatory) Directory where file objects will exist.  Directory must exist immediately
  under 'public' directory.  Must match value provided to prism_play_cli.py
  * 'channels': (Default: 1) Number of channels to create drivers for
* Developer callable driver methods:
  * get_references: Returns list of passed references (or None)
  * get_artifact_path: Returns path to artifact, updated to Prisms public/<work_dir> directory
  location
  * get_play_received: Returns True if PrismPlay driver triggered test play


