# FEDSync
FEDSync is software designed to control the [FED3 Unit](https://github.com/KravitzLabDevices/FED3) over a serial connection

<img src="https://github.com/cora-reef/FEDSync/blob/6855d8618207daa3d5228b3b8d4723c681748c1d/photos/FEDSync-UI.png" width="500em">

## Requirements
### Linux
For Linux you will need to download and run the python source code. 
Python Modules needed
1. `pyqt5`
2. `pySerial`

### Windows
Windows has a bundled executable which can be downloaded from releases.


## Arduino Setup
A [custom library](https://github.com/cora-reef/FED3_library) for the FED3 device is currently required.


## How to Use
1. Follow the installation guide for the FED3 library from the main github.
2. Replace the Arduino Library code with the custom fork mentioned above
3. You will need to modify the your experiments code to expose the library modifications to serial
Using the ClassicFED3 example code as a base
We will add the RTC Clock header to the includes

```cpp
#include "RTClib.h"
```
<img src="https://github.com/cora-reef/FEDSync/blob/630ab35b1fbb30ba1ebb1ad6f0fecc5fc9db10b9/photos/header.png" width="">

Then we will modify the `setup` function to enable the serial functions
```cpp
void setup() {
  ...
  fed3.disableSleep();
  fed3.SerialLogging = true;
  Serial.begin(57600);
}
```
<img src="https://github.com/cora-reef/FEDSync/blob/630ab35b1fbb30ba1ebb1ad6f0fecc5fc9db10b9/photos/setup.png" width="">

Adding a function to parse commands sent by FEDSync
```cpp
void parse_command() {
  while(Serial.available()) {
    String command = Serial.readStringUntil('\0');
    if(command == "Reset"){
      fed3.rest_vars();

    } else if(command == "Headers") {
      fed3.sendHeaders();

    } else if(command == "Time") {
      char time[100];
      Serial.readStringUntil('\0').toCharArray(time, 99);
      rtc.adjust(DateTime(time));
      Serial.print(time);
      Serial.write((byte)0);

    } else {
      Serial.print(command);
      Serial.write((byte)0);
    }
  }
}
```

Before we decalre `loop` we are going to add a boolean that will to wait for the fed device to be used.
```cpp
bool started = false;
void loop() {...
```


Lastly modify the `loop` to wait for a left poke before starting the device, this will let us talk to the device before we start the experiment
```cpp
void loop() {
  while(!started) {
    parse_command();
    if(fed3.Left) started = true;
  }
  ...
```
<img src="https://github.com/cora-reef/FEDSync/blob/630ab35b1fbb30ba1ebb1ad6f0fecc5fc9db10b9/photos/loop.png" width="">
