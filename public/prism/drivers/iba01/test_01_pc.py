from time import sleep
import ampy.pyboard as pyboard

pyb = pyboard.Pyboard("/dev/ttyACM0")
pyb.enter_raw_repl()

data, data_err = pyb.exec_raw("import test_01\n")
print(data, data_err)

for i in range(100):
    data, data_err = pyb.exec_raw("test_01.foo.get()\n")
    print(i, data, data_err)
    sleep(1)

