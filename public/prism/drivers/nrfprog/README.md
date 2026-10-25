# Nordic nRF Programmer (nrfjprog)

## Related links

https://www.nordicsemi.com/Products/Development-tools/nRF-Command-Line-Tools/Download

Nordic has archived the nRF Command Line Tools (replaced by nRF Util), the
last release is 10.24.2.  It is still available for download.


## Installing nRF Command Line Tools

This driver runs `nrfjprog` from the nRF Command Line Tools.  The tools are
installed on each Prism station, they are not part of the scripts that Lente
syncs to the station.

The driver expects the tool at,

    ~/scripts/public/tools/nrf-command-line-tools/bin/nrfjprog

`public/tools/` is ignored by git and is not touched by a Lente script sync.
Prism sees it as `/app/public/tools/` through its existing `public` mount.

`nrfjprog` also needs the Segger J-Link library.  This is already installed
in the Prism Docker image (`/opt/SEGGER/JLink`), so only the Nordic tools are
installed here.  The image uses J-Link V8.72: with J-Link V9.x, nrfjprog
10.24.2 prints `JLinkARM.dll reported error -256` on every call and takes
about 7 s longer to connect to the probe.

* Download the Linux x86 64 `tar.gz` (not the `deb`) of version 10.24.2,
  `nrf-command-line-tools-10.24.2_linux-amd64.tar.gz`.
  By installing you accept the Nordic licence agreement.
* As the station user (not root), unpack only the `nrf-command-line-tools`
  folder.  The J-Link package in the tar is not needed.

      mkdir -p ~/scripts/public/tools
      tar xzf ~/Downloads/nrf-command-line-tools-10.24.2_linux-amd64.tar.gz \
          -C ~/scripts/public/tools ./nrf-command-line-tools

* Check the tool runs inside Prism (it will not run on the host unless J-Link
  is installed there too),

      docker exec prism /app/public/tools/nrf-command-line-tools/bin/nrfjprog --version

  which should show,

      nrfjprog version: 10.24.2 external
      JLinkARM.dll version: 8.72

When Prism loads a script that uses this driver, `discover_channels()` runs
`nrfjprog --version`.  If the tool is missing or cannot load the J-Link
library, the driver logs an error and shows a Prism notice that points to
this README.

To uninstall, delete `~/scripts/public/tools/nrf-command-line-tools`.


## Debugging

With a J-Link connected, list the probes from inside Prism,

    $ docker exec prism /app/public/tools/nrf-command-line-tools/bin/nrfjprog --ids
    821009733
    821009774

To confirm `hwdrv_nrfjprog.py` can find the Seggers, run it with the working
directory set to `~/git/scripts` (in PyCharm, or from the command line).
This needs J-Link installed on the host.

    INFO:hwdrv_nrfjprog.py:Start
    INFO:hwdrv_nrfjprog.py:nrfjprog 10.24.2, JLinkARM 8.72
    INFO:hwdrv_nrfjprog.py:[{'id': 0, ..., 'unique_id': '821009733', 'usb_path': '/devices/pci0000:00/0000:00:08.1/0000:03:00.3/usb1/1-2/1-2.1/1-2.1.4/1-2.1.4.2', 'version': '0.0.1'}, {'id': 1, ..., 'unique_id': '821009774', ...}]
    INFO:sys_log:HWDriver:hwdrv_nrfjprog.py: Found 2!
    INFO:hwdrv_nrfjprog.py:Done: 2 channels
    INFO:root:Number channels: 2

The CLI help (`nrfjprog --help`) lists all commands, for example `--program`,
`--recover`, `--sectorerase`, `--verify`, `--reset`.
