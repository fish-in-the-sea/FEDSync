# FEDSync
FEDSync is software designed to control the [FED3 Unit](https://github.com/KravitzLabDevices/FED3) over a serial connection

<img src="https://github.com/cora-reef/FEDSync/blob/739e7d2429bd06c0ba4a3f5a44e0e874d1a3b4f6/photos/FED3Sync-UI.png" width="500em">

## Requirements
FEDSync requires
1. `pyqt5`
2. `pySerial`
3. And a currently [custom library](https://github.com/cora-reef/FED3_library) for the FED3 device

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

Lastly modify the `loop` function to check and use the serial connection
```cpp
void loop() {
  while(Serial.available()) {
    String command =  Serial.readStringUntil('\0');
    if(command == "Time") {
      char time[100];
      Serial.readStringUntil('\0').toCharArray(time, 99);
      rtc.adjust(DateTime(time));
      Serial.print(time);
    } else if(command == "Reset") {
      fed3.rest_vars();
    } else if(command == "Headers"){
      fed3.sendHeaders();
    }
    Serial.print('\0');
  }
  ...
```
<img src="https://github.com/cora-reef/FEDSync/blob/630ab35b1fbb30ba1ebb1ad6f0fecc5fc9db10b9/photos/loop.png" width="">
