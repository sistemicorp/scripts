# STMicroelectronics ST-LINK/V3

## Related links

https://www.st.com/en/development-tools/stm32cubeprog.html


## Installing ST-LINK/V3 drivers

* Install STMCubeProgrammer from STM website
* Copy over the files to this folder (`./public/prism/drivers/stlinkv3mods/STM32CubeProgrammer`),
* In order to debug running the STM32CubeProgrammer_CLI you can do the following,
  * Edit the `hwdrv_stlinkv3mods.py` file by changing the import and commenting out the `pub_notice()` function
  * Run the script locally from the command line, 


    (.venv) martin@martin-ThinkPad-L13-Gen-2a:~/git/scripts$ python public/prism/drivers/stlinkv3mods/hwdrv_stlinkv3mods.py 
    INFO:hwdrv_stlinkv3mods.py:Start
    INFO:hwdrv_stlinkv3mods.py:Found device: b'STLINK-V3', sn 3600383234511733353533, /devices/pci0000:00/0000:00:08.1/0000:07:00.4/usb3/3-2/3-2.4
    INFO:root:./public/prism/drivers/stlinkv3mods/bin/STM32_Programmer_CLI sn=3600383234511733353533 --version
    INFO:hwdrv_stlinkv3mods.py:version: CompletedProcess(args=['./public/prism/drivers/stlinkv3mods/bin/STM32_Programmer_CLI', 'sn=3600383234511733353533', '--version'], returncode=0, stdout='\x1b[36m\x1b[01m      -------------------------------------------------------------------\n\x1b[39;49m\x1b[0m\x1b[36m\x1b[01m                        STM32CubeProgrammer v2.20.0                  \n\x1b[39;49m\x1b[0m\x1b[36m\x1b[01m      -------------------------------------------------------------------\n\n\x1b[39;49m\x1b[0m\x1b[39;49mSTM32CubeProgrammer version: 2.20.0 \n\n\x1b[39;49m\x1b[0m', stderr='./public/prism/drivers/stlinkv3mods/bin/STM32_Programmer_CLI: ./public/prism/drivers/stlinkv3mods/bin/libcrypto.so.1.1: no version information available (required by ./public/prism/drivers/stlinkv3mods/bin/STM32_Programmer_CLI)\n./public/prism/drivers/stlinkv3mods/bin/STM32_Programmer_CLI: ./public/prism/drivers/stlinkv3mods/bin/libcrypto.so.1.1: no version information available (required by ./public/prism/drivers/stlinkv3mods/bin/STM32_Programmer_CLI)\n')
    INFO:hwdrv_stlinkv3mods.py:[{'id': 0, 'hwdrv': <STLINK.STLINKprog object at 0x7420197daf50>, 'close': None, 'play': None, 'show_pass_fail': None, 'show_msg': None, 'unique_id': '3600383234511733353533', 'usb_path': '/devices/pci0000:00/0000:00:08.1/0000:07:00.4/usb3/3-2/3-2.4', 'version': '0.0.1'}]
    INFO:hwdrv_stlinkv3mods.py:Done: 1 channels
    INFO:root:Number channels: 1

* Run the example script `public/prism/scripts/example/stlinkv3mods/check_stlink_0.scr` to confirm it works as well from the Prism GUI.
