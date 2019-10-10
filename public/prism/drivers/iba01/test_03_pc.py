from time import sleep
import ampy.pyboard as pyboard

pyb = pyboard.Pyboard("/dev/ttyACM0")
pyb.enter_raw_repl()

data, data_err = pyb.exec_raw("import test_03\n")
print(data, data_err)

data, data_err = pyb.exec_raw("test_03.foo.put('now is the time')\n", timeout=10, data_consumer=None)
print(data, data_err)
sleep(0.1)
for i in range(10000):
    data, data_err = pyb.exec_raw("test_03.foo.ret(method='bar', all=False)\n", timeout=10, data_consumer=None)
    print(i, data, data_err)
    sleep(0.1)

