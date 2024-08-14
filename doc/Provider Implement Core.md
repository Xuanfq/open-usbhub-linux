
# Provider Implement Core

## Topological

### Conclusion

**Tree of `lsusb`**
```log
T0 BusID 0
  |__ T1 PortID If
    |__ T2 PortID If
      |__ T3 PortID IfID0
      |__ T3 PortID IfID1
      |__ T3 PortID IfID2
```

Mapping: `$T0BusID-$T1PortID.$T2PortID.$T3PortID....$TnPortID:1.$TnIfID`
USB Available Devices: `Class` do not include `hub`
Other Rules: 
    1. IfID0 Device [e.g. ttyUSB0] < IfID1 Device [e.g. ttyUSB1] < IfID2 Device [e.g. ttyUSB2]

**Device of USB**
```shell
cd /sys/bus/usb/devices/
ls $T0BusID-$T1PortID.$T2PortID.$T3PortID....$TnPortID:1.$TnIfID  # catch ttyXXXn, e.g. below: ttyUSB1
# authorized         bInterfaceNumber    bNumEndpoints  ep_81      interface  subsystem             uevent
# bAlternateSetting  bInterfaceProtocol  driver         gpio       modalias   supports_autosuspend
# bInterfaceClass    bInterfaceSubClass  ep_02          gpiochip5  power      ttyUSB1
ls /dev/ttyXXXn
```


### Investigation

- Host 1
```shell
root@root:/sys/bus/usb/devices# lsusb -t -v
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/7p, 5000M
    ID 1d6b:0003 Linux Foundation 3.0 root hub
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/9p, 480M
    ID 1d6b:0002 Linux Foundation 2.0 root hub
    |__ Port 3: Dev 52, If 2, Class=Vendor Specific Class, Driver=cp210x, 12M
        ID 10c4:ea71 Silicon Labs CP2108 Quad UART Bridge
    |__ Port 3: Dev 52, If 0, Class=Vendor Specific Class, Driver=cp210x, 12M
        ID 10c4:ea71 Silicon Labs CP2108 Quad UART Bridge
    |__ Port 3: Dev 52, If 3, Class=Vendor Specific Class, Driver=cp210x, 12M
        ID 10c4:ea71 Silicon Labs CP2108 Quad UART Bridge
    |__ Port 3: Dev 52, If 1, Class=Vendor Specific Class, Driver=cp210x, 12M
        ID 10c4:ea71 Silicon Labs CP2108 Quad UART Bridge
    |__ Port 7: Dev 4, If 0, Class=Video, Driver=uvcvideo, 480M
        ID 04f2:b5e0 Chicony Electronics Co., Ltd
    |__ Port 7: Dev 4, If 1, Class=Video, Driver=uvcvideo, 480M
        ID 04f2:b5e0 Chicony Electronics Co., Ltd
    |__ Port 9: Dev 5, If 0, Class=Wireless, Driver=btusb, 12M
        ID 8087:0aaa Intel Corp. Bluetooth 9460/9560 Jefferson Peak (JfP)
    |__ Port 9: Dev 5, If 1, Class=Wireless, Driver=btusb, 12M
        ID 8087:0aaa Intel Corp. Bluetooth 9460/9560 Jefferson Peak (JfP)
root@root:/sys/bus/usb/devices# ll /sys/bus/usb/devices
total 0
drwxr-xr-x 2 root root 0 Apr 16 17:31 ./
drwxr-xr-x 4 root root 0 Apr 16 17:31 ../
lrwxrwxrwx 1 root root 0 Apr 16 17:31 1-0:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-0:1.0/
lrwxrwxrwx 1 root root 0 Jul 10 16:43 1-3 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-3/
lrwxrwxrwx 1 root root 0 Jul 10 16:43 1-3:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-3/1-3:1.0/
lrwxrwxrwx 1 root root 0 Jul 10 16:43 1-3:1.1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-3/1-3:1.1/
lrwxrwxrwx 1 root root 0 Jul 10 16:43 1-3:1.2 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-3/1-3:1.2/
lrwxrwxrwx 1 root root 0 Jul 10 16:43 1-3:1.3 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-3/1-3:1.3/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 1-7 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-7/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 1-7:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-7/1-7:1.0/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 1-7:1.1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-7/1-7:1.1/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 1-9 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-9/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 1-9:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-9/1-9:1.0/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 1-9:1.1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-9/1-9:1.1/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 2-0:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb2/2-0:1.0/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 usb1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/
lrwxrwxrwx 1 root root 0 Apr 16 17:31 usb2 -> ../../../devices/pci0000:00/0000:00:15.0/usb2/
root@root:/sys/bus/usb/devices# ls 1-3:1.0
authorized         bInterfaceNumber    bNumEndpoints  ep_81          gpiochip4  physical_location  supports_autosuspend
bAlternateSetting  bInterfaceProtocol  driver         firmware_node  interface  power              ttyUSB0
bInterfaceClass    bInterfaceSubClass  ep_01          gpio           modalias   subsystem          uevent
root@root:/sys/bus/usb/devices# ls 1-3:1.1
authorized         bInterfaceNumber    bNumEndpoints  ep_82          modalias           subsystem             uevent
bAlternateSetting  bInterfaceProtocol  driver         firmware_node  physical_location  supports_autosuspend
bInterfaceClass    bInterfaceSubClass  ep_02          interface      power              ttyUSB1
root@root:/sys/bus/usb/devices# ls /dev/ttyUSB0
/dev/ttyUSB0
root@root:/sys/bus/usb/devices# ls /dev/ttyUSB1
/dev/ttyUSB1
root@root:/sys/bus/usb/devices#
```

- Host 2
```shell
root@dev:/sys/bus/usb/devices# lsusb -t -v
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/7p, 5000M
    ID 1d6b:0003 Linux Foundation 3.0 root hub
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/9p, 480M
    ID 1d6b:0002 Linux Foundation 2.0 root hub
    |__ Port 1: Dev 33, If 0, Class=Hub, Driver=hub/7p, 480M
        ID 1a40:0201 Terminus Technology Inc. FE 2.1 7-port Hub
        |__ Port 7: Dev 39, If 0, Class=Hub, Driver=hub/4p, 480M
            ID 1a40:0101 Terminus Technology Inc. Hub
        |__ Port 3: Dev 36, If 0, Class=Hub, Driver=hub/4p, 480M
            ID 1a40:0101 Terminus Technology Inc. Hub
        |__ Port 1: Dev 34, If 0, Class=Hub, Driver=hub/4p, 480M
            ID 1a40:0101 Terminus Technology Inc. Hub
        |__ Port 6: Dev 38, If 0, Class=Hub, Driver=hub/4p, 480M
            ID 1a40:0101 Terminus Technology Inc. Hub
        |__ Port 4: Dev 37, If 0, Class=Hub, Driver=hub/4p, 480M
            ID 1a40:0101 Terminus Technology Inc. Hub
            |__ Port 2: Dev 41, If 0, Class=Vendor Specific Class, Driver=ftdi_sio, 12M
                ID 0403:6015 Future Technology Devices International, Ltd Bridge(I2C/SPI/UART/FIFO)
            |__ Port 3: Dev 42, If 0, Class=Vendor Specific Class, Driver=ftdi_sio, 12M
                ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC
        |__ Port 2: Dev 35, If 0, Class=Hub, Driver=hub/4p, 480M
            ID 1a40:0101 Terminus Technology Inc. Hub
    |__ Port 7: Dev 2, If 0, Class=Video, Driver=uvcvideo, 480M
        ID 0408:a031 Quanta Computer, Inc.
    |__ Port 7: Dev 2, If 1, Class=Video, Driver=uvcvideo, 480M
        ID 0408:a031 Quanta Computer, Inc.
    |__ Port 9: Dev 3, If 0, Class=Wireless, Driver=btusb, 12M
        ID 8087:0aaa Intel Corp. Bluetooth 9460/9560 Jefferson Peak (JfP)
    |__ Port 9: Dev 3, If 1, Class=Wireless, Driver=btusb, 12M
        ID 8087:0aaa Intel Corp. Bluetooth 9460/9560 Jefferson Peak (JfP)
root@dev:/sys/bus/usb/devices# ll /sys/bus/usb/devices
total 0
drwxr-xr-x 2 root root 0 Jul 11 10:57 ./
drwxr-xr-x 4 root root 0 Jul 11 10:57 ../
lrwxrwxrwx 1 root root 0 Jul 11 10:58 1-0:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-0:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 02:19 1-1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/
lrwxrwxrwx 1 root root 0 Jul 12 02:19 1-1.1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.1/
lrwxrwxrwx 1 root root 0 Jul 12 02:11 1-1:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 02:11 1-1.1:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.1/1-1.1:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 02:19 1-1.2 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.2/
lrwxrwxrwx 1 root root 0 Jul 12 02:11 1-1.2:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.2/1-1.2:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 02:19 1-1.3 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.3/
lrwxrwxrwx 1 root root 0 Jul 12 02:11 1-1.3:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.3/1-1.3:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 02:19 1-1.4 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.4/
lrwxrwxrwx 1 root root 0 Jul 12 02:11 1-1.4:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.4/1-1.4:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 04:08 1-1.4.2 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.4/1-1.4.2/
lrwxrwxrwx 1 root root 0 Jul 12 03:34 1-1.4.2:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.4/1-1.4.2/1-1.4.2:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 06:06 1-1.4.3 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.4/1-1.4.3/
lrwxrwxrwx 1 root root 0 Jul 12 06:06 1-1.4.3:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.4/1-1.4.3/1-1.4.3:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 02:19 1-1.6 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.6/
lrwxrwxrwx 1 root root 0 Jul 12 02:11 1-1.6:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.6/1-1.6:1.0/
lrwxrwxrwx 1 root root 0 Jul 12 02:19 1-1.7 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.7/
lrwxrwxrwx 1 root root 0 Jul 12 02:11 1-1.7:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-1/1-1.7/1-1.7:1.0/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 1-7 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-7/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 1-7:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-7/1-7:1.0/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 1-7:1.1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-7/1-7:1.1/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 1-9 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-9/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 1-9:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-9/1-9:1.0/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 1-9:1.1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/1-9/1-9:1.1/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 2-0:1.0 -> ../../../devices/pci0000:00/0000:00:15.0/usb2/2-0:1.0/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 usb1 -> ../../../devices/pci0000:00/0000:00:15.0/usb1/
lrwxrwxrwx 1 root root 0 Jul 11 10:58 usb2 -> ../../../devices/pci0000:00/0000:00:15.0/usb2/
root@dev:/sys/bus/usb/devices# ls 1-1.4.3:1.0
authorized         bInterfaceNumber    bNumEndpoints  ep_81      interface  subsystem             uevent
bAlternateSetting  bInterfaceProtocol  driver         gpio       modalias   supports_autosuspend
bInterfaceClass    bInterfaceSubClass  ep_02          gpiochip5  power      ttyUSB1
root@dev:/sys/bus/usb/devices# ls /dev/ttyUSB1
/dev/ttyUSB1
root@dev:/sys/bus/usb/devices#
```


## Vendor

### Sipolar 西普来 A-805P 20口USB2.0集成器
USB Hub Tech Vendor: Terminus Technology Inc.


#### Topo

- OS Scanning from Ubuntu
```shell
|__ Port n: Dev 43, If 0, Class=Hub, Driver=hub/7p, 480M
    ID 1a40:0201 Terminus Technology Inc. FE 2.1 7-port Hub
    |__ Port 1: Dev 44, If 0, Class=Hub, Driver=hub/4p, 480M
        ID 1a40:0101 Terminus Technology Inc. Hub
    |__ Port 6: Dev 48, If 0, Class=Hub, Driver=hub/4p, 480M
        ID 1a40:0101 Terminus Technology Inc. Hub
    |__ Port 4: Dev 47, If 0, Class=Hub, Driver=hub/4p, 480M
        ID 1a40:0101 Terminus Technology Inc. Hub
    |__ Port 2: Dev 45, If 0, Class=Hub, Driver=hub/4p, 480M
        ID 1a40:0101 Terminus Technology Inc. Hub
    |__ Port 7: Dev 49, If 0, Class=Hub, Driver=hub/4p, 480M
        ID 1a40:0101 Terminus Technology Inc. Hub
    |__ Port 3: Dev 46, If 0, Class=Hub, Driver=hub/4p, 480M
        ID 1a40:0101 Terminus Technology Inc. Hub
```

- Physical
```log
HUB Root 4p Port-7		
    Sipolar 1	Port-1
    Sipolar 2	Port-2
    Sipolar 3	Port-3
HUB Root 4p Port-3		
    Sipolar 4	Port-2
    Sipolar 5	Port-3
    Sipolar 6	Port-4
HUB Root 4p Port-4		
    Sipolar 7	Port-1
    Sipolar 8	Port-2
    Sipolar 9	Port-3
    Sipolar 10	Port-4
HUB Root 4p Port-6		
    Sipolar 11	Port-1
    Sipolar 12	Port-2
    Sipolar 13	Port-4
HUB Root 4p Port-2		
    Sipolar 14	Port-2
    Sipolar 15	Port-3
    Sipolar 16	Port-4
HUB Root 4p  Port-1		
    Sipolar 17	Port-1
    Sipolar 18	Port-2
    Sipolar 19	Port-3
    Sipolar 20	Port-4
```




