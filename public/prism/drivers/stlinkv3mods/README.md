# STMicroelectronics ST-LINK/V3

## Related links

https://www.st.com/en/development-tools/stm32cubeprog.html


## Installing STM32CubeProgrammer

This driver runs the `STM32_Programmer_CLI` tool from STM32CubeProgrammer.
The tool is installed on each Prism station, it is not part of the scripts
that Lente syncs to the station.

The driver expects the tool at,

    ~/scripts/public/tools/STM32CubeProgrammer/bin/STM32_Programmer_CLI

`public/tools/` is ignored by git and is not touched by a Lente script sync.
Prism sees it as `/app/public/tools/` through its existing `public` mount.

* Download STM32CubeProgrammer for Linux from the ST website (a free myST
  account is required). Tested with v2.22.0, `SetupSTM32CubeProgrammer_linux_64.zip`.
* As the station user (not root), unzip and run the installer. By installing
  you accept the ST licence agreement.

      mkdir -p ~/stm32cubeprog && cd ~/stm32cubeprog
      unzip ~/Downloads/SetupSTM32CubeProgrammer_linux_64.zip
      echo "INSTALL_PATH=$HOME/scripts/public/tools/STM32CubeProgrammer" > install.properties
      ./SetupSTM32CubeProgrammer-2.22.0.linux -options install.properties

  For the interactive installer, run `./SetupSTM32CubeProgrammer-2.22.0.linux`
  (or add `-console` on a headless station) and set the install path to
  `~/scripts/public/tools/STM32CubeProgrammer`.

* Check the tool runs,

      cd ~/scripts
      ./public/tools/STM32CubeProgrammer/bin/STM32_Programmer_CLI --version

* The installer download folder (`~/stm32cubeprog`) can be deleted.

When Prism loads a script that uses this driver, `discover_channels()` runs
`STM32_Programmer_CLI --version`. If the tool is missing or does not run, the
driver logs an error and shows a Prism notice that points to this README.

To uninstall, delete `~/scripts/public/tools/STM32CubeProgrammer`.


## Debugging

To debug running `STM32_Programmer_CLI` you can do the following,

* Edit the `hwdrv_stlinkv3mods.py` file by changing the import and commenting out the `pub_notice()` function
* Run the script locally from the command line,

      (.venv) martin@martin-ThinkPad-L13-Gen-2a:~/git/scripts$ python public/prism/drivers/stlinkv3mods/hwdrv_stlinkv3mods.py
      INFO:hwdrv_stlinkv3mods.py:Start
      INFO:hwdrv_stlinkv3mods.py:STM32CubeProgrammer version: 2.22.0
      INFO:hwdrv_stlinkv3mods.py:Found device: b'STLINK-V3', sn 3600383234511733353533, /devices/pci0000:00/0000:00:08.1/0000:07:00.4/usb3/3-2/3-2.4
      INFO:root:./public/tools/STM32CubeProgrammer/bin/STM32_Programmer_CLI sn=3600383234511733353533 --version
      ...
      INFO:hwdrv_stlinkv3mods.py:Done: 1 channels
      INFO:root:Number channels: 1

* Run the example script `public/prism/scripts/example/stlinkv3mods/check_stlink_0.scr` to confirm it works as well from the Prism GUI.
