FTCAN 2.0 protocol
Document release control ........................................................................................................2
FTCAN 2.0 protocol ..................................................................................................................4
Physical layer ........................................................................................................................ 4
Features................................................................................................................................ 4
IDENTIFICATION ...................................................................................................................4
ProductID ......................................................................................................................... 4
DataFieldID ....................................................................................................................... 5
MessageID ........................................................................................................................ 5
DATA FIELD ........................................................................................................................... 6
DataFieldID 0x00: Standard CAN ......................................................................................6
DataFieldID 0x01: Standard CAN Bridge (bridge, gateway ou converter) ........................6
DataFieldID 0x02: FTCAN 2.0 ............................................................................................6
DataFieldID 0x03: FTCAN 2.0 Bridge (bridge, gateway ou converter) ..............................8
Attachements ........................................................................................................................... 9
ProductID’s list ..................................................................................................................... 9
MessageID’s list ..................................................................................................................10
•
•
0x0FF, 0x1FF, 0x2FF e 0x3FF – Real time reading broadcast ..................................10
0x600 ~ 0x608 – Real time simple broadcast..........................................................11
MeasureIDs ........................................................................................................................12
Simplified packets ..............................................................................................................25
Connector Pinout ...............................................................................................................27
Examples ............................................................................................................................28
Example 1: Standard CAN layout – Single packet with RPM value .................................28
Example 2: Standard CAN layout – Single packet with RPM and TPS values ..................29
Example 3: FTCAN layout - Single packet with RPM value .............................................30
Example 4: FTCAN layout - Multiple packets with 5 different values .............................31
FTCAN2.0 segmented packet flowchart .........................................................................33
1
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Document release control
Release
Date
001
04/14/2016
002
06/21/2016
2
003
004
005
00606/24/2016
06/27/2016
07/20/2016
12/27/2016
007
00801/18/2017
04/07/2017
00912/12/2017
010
011
012
013
014
01501/05/2018
03/15/2018
10/16/2018
11/26/2018
02/21/2019
04/17/2019
01605/20/2019
017
01808/21/2019
11/28/2019
01907/20/2020
Changes
Initial release
Added information about data endianness and signal
Corrected the MAP value on the example of page 17.
Added connector pinout information
Added source information on the DataID list
Added broadcast rate information on the DataID list
Added FTSPARK’s CAN information
Added GND signal in the CAN connector drawing
Added the possibles MeasureIDs for one DataID in the
MeasureID table
Corrected text typos
Added information about external keypad
Added new DataIDs for button operations
Added new DataIDs for temperature reading
Modified the FTSpark’s ProductID range allowing 2 units to be
used on the CAN bus
Added PitLimit Switch DataID
Added new DataIDs (0x008E to 0x0115)
Added new DataIDs (0x0116 to 0x0119)
Removed unused DataIDs related to aborted projects
Added new switchpanel options
Added new DataIDs (0x011A to 0x0136)
Changed individual ECU´s name to “PowerFT ECU”
Changed injection duty cycle’s broadcast rate from 100 to
10Hz
Added new MessagesIDs (0x0600, 0x0601 e 0x0602)
Added new DataIDs (0x0137 to 0x0138)
Added new Injector Driver ProdcutID
Added new DataIDs (0x0148 to 0x0153)
Added segment packet flowchart
Added EGT-4’s ProductIDs
Modified the maximum number of gears from 6 to 10
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
3
02008/19/2020
02108/13/2021
02203/04/2022
02304/06/2022
024
02622/06/2022
24/08/2022
02708/05/2023
Added new DataIDs (0x0154 to 0x016A)
Added FTSpark B ProductID
Added warning about ECU´s broadcast transmission rate
variation under hi RPM
Added information about the ECU’s simplified broadcast
packets
Added information about the ECU’s simplified broadcast
packets
Added new MessagesIDs (0x0608)
Added new Measure ID (0x0170 ~ 0x01B8)
Added brake pressure in the simplified packets
Fixed ECU O2 Sensor Unit information (note 3)
Fixed MeasureID sequence error starting at 0x02E0
Added EV DataID
Added TPMS device information
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
FTCAN 2.0 protocol
Physical layer
CAN 2.0B extended mode
Rate: 1Mbps
Features
In this document we will approach the implementation of a custom protocol (FTCAN)
running on top of a CAN 2.0B physical layer. One main feature of the FTCAN protocol is
to provide a means to segment a large stream of data into many smaller CAN packets.
We will consider a CAN FRAME as indicated below:
29 bits
IDENTIFICATION
CAN FRAME
0 to 8 bytes
DATA FIELD
IDENTIFICATION
The FTCAN will use the 29 bits of the IDENTIFICATION header to identify the device that
originated the message. The 29 bits will be divided in order to provide information about:
the unique product identifier, type of data and the type of message that is being sent.
The bit division was planned in order to have multiple message priorities for the same
type of product, and to have multiple priorities for the many different products inside the
same CAN physical layer.
Bits 28 to 14 (15 bits)
ProductID
IDENTIFICATION (29 bits)
Bits 13 to 11 (3 bits)
DataFieldID
Bits 10 to 0 (11 bits)
MessageID
ProductID
Identifies the product that has sent the message. The lower the ProductID the higher is
the priority in the CAN bus. In the network two devices that are the same type of product
(two O2 sensors for example) cannot have the same ProductID. In order to differentiate
two products of the same type the ProductID bits are divided as show below.
ProductID (15 bits)
Bit 14 to 5 (10 bits)
Bits 4 to 0 (5 bits)
ProductTypeID
Unique identifier
4
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Each product that wants to send data to the CAN bus must have a unique identifier.
Devices that will only receive data from the CAN bus doesn’t need to have a unique ID.
The ProductIDs are divided in priority ranges:
•
•
•
•
Critical priority:
High priority:
Medium priority:
Low priority:
0x0000 to 0x1FFF
0x2000 to 0x3FFF
0x4000 to 0x5FFF
0x6000 to 0x7FFF
A list with all the possible ProductTypeIDs is presented later in this document.
DataFieldID
Identifies the type of data structure that is being sent in the CAN FRAME -> DATA FIELD.
There are 4 possible data layouts:
•
•
•
•
0x00: Standard CAN data field
0x01: Standard CAN data field coming from/going to a bus converter.
0x02: FTCAN 2.0 data field
0x03: FTCAN 2.0 data field coming from/going to a bus converter.
MessageID
Identifies the data in the DATA FIELD. Example: commands, configuration data, real time
readings, etc. The lower the MessageID the higher is the priority. The MessageID’s most
significant bit is reserved in order to identify a response from a command:
Bit 10
Response (value 1)
MessageID (11 bits)
Bits 9 to 0 (10 bits)
Message code
The priorities ranges are:
•
•
•
•
Critical priority:
High priority:
Medium priority:
Low priority:
0x000 a 0x0FF
0x100 a 0x1FF
0x200 a 0x2FF
0x300 a 0x3FF
A list with all the possible MessageIDs is presented later in this document.
5
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
DATA FIELD
The DATA FIELD can have up to 8 data layouts accordingly to the DataFieldID’s value. All
values in the DATA FIELD are transmitted as big-endian.
DataFieldID 0x00: Standard CAN
In this data layout all 8 bytes of the DATA FIELD are used as valid data (PAYLOAD). All data
are transmitted in one shot since this mode doesn’t implement data segmentation.
0
1
2
DATA FIELD (1 to 8 bytes)
3
4
5
PAYLOAD
6
7
DataFieldID 0x01: Standard CAN Bridge (bridge, gateway ou converter)
In this data layout all 8 bytes of the DATA FIELD will be forwarded by the bus converter.
The DataFieldID (0x01) is also used to identify packets that are originated outside the CAN
bus. Bridge examples are: Standalone USB-CAN converter, FT500’s USB-CAN bridge, etc.
0
1
2
DATA FIELD (1 to 8 bytes)
3
4
5
PAYLOAD
6
7
DataFieldID 0x02: FTCAN 2.0
This is the DataFieldID that all FuelTech’s devices will use to communicated with each
other in the CAN bus. The data segmentation feature is implemented in this type of data
layout. As can be seen in the diagrams below the segmentation feature uses the first byte
of the DATA FIELD to indicate which segment of the following bytes is. There can be 2
types of packets:
• Single packet (all data is transmitted in one CAN packet)
• Segmented packet (data is transmitted in multiples CAN packets)
Single packet
The first byte of the DATA FIELD will have the value of 0xFF. The following 7 bytes will
have the message data (PAYLOAD).
6
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
0
0xFF
1
2
DATA FIELD (1 to 8 bytes)
3
4
5
PAYLOAD
6
7
Segmented packet
In the first byte of the DATA FIELD there will be values ranging from 0x00 to 0xFE. The
first segment will have the 0x00 value and the following packets will contain 0x01, 0x02
and so on. In the first segment the 2 bytes following the 0x00 value contain the
segmentation data.
First segment
0
0x00
1
2
SEGMENTATION
DATA
Second segment
0
0x01
1
2
Third segment (if present)
0
1
2
0x02
.
.
.
Last segment (if present)
0
0xFE
1
2
DATA FIELD (8 bytes)
3
4
5
PAYLOAD
67
DATA FIELD (1 to 8 bytes)
3
4
5
PAYLOAD67
DATA FIELD (1 to 8 bytes)
3
4
5
PAYLOAD67
DATA FIELD (1 to 8 bytes)
3
4
5
PAYLOAD67
The maximum PAYLOAD length will be: 5 + (0xFD * 7) = 1776 bytes.
7
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
The segmentation data contains the following information:
SEGMENTATION DATA (2 bytes)
Bytes
1
2
Bits
15 14 13 12 11 10 9 8 7 6 5 4 3 2 1
RFU RFU RFU RFU RFU
PAYLOAD total length (in bytes)
0
RUF: Reserved for Future Use
DataFieldID 0x03: FTCAN 2.0 Bridge (bridge, gateway ou converter)
This DataFieldID uses the same data layout from DataFieldID’s 0x02 when the data is
going to or coming from a BUS converter.
8
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Attachements
ProductID’s list
Since the 5 least significant bits of the ProductID are used for the unique value the FTCAN
protocol can have up to 32 devices of the same product type at the same time. The unique
value will range from 0x00 to 0x1F. The limit for different products types will be 1024.
Priority
9
ProductID
ProductTypeID
Range
Start
Finish
Critical-----0x0FFF0x0FFF
High
High
High
High
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Medium
Low
Low
Reserved
Reserved
Reserved0x0140
0x0141
0x0142
0x0150
0x023F
0x0240
0x0241
0x0242
0x0243
0x0243
0x0244
0x0244
0x0244
0x0244
0x0245
0x0246
0x0280
0x0281
0x0282
…
0x02E4
0x0340
0x0380
-----
-----
-----0x2800
0x2820
0x2840
0x2A00
0x47E0
0x4800
0x4820
0x4840
0x4860
0x4861
0x4880
0x4882
0x4884
0x4886
0x48A0
0x48C0
0x5000
0x5020
0x5040
…
0x5C80
0x6800
0x7000
0x0800
0x0880
0x09000x281F
0x283F
0x285F
0x2A1F
0x47FF
0x481F
0x483F
0x485F
0x4860
0x4861
0x4881
0x4883
0x4885
0x4887
0x48A0
0x48DF
0x501F
0x503F
0x505F
…
0x5C9F
0x681F
0x7000
0x0800
0x0880
0x0900
Product Type
Device searching a ProductID
(unique value undefined)
Gear Controller
Knock Meter
Boost Controller 2
Injector Driver
Input Expander
WBO2 Nano
WBO2 Slim
Alcohol O2
FTSPARK A
FTSPARK B
Switchpad-8
Switchpad-4
Switchpad-5
Switchpad-8 mini
TPMS reader
Reserved for Future Use
FT500 ECU
FT600 ECU
First reserved range for future ECUs
…
Last reserved range for future ECUs
Reserved for Future Use
Internal use
FuelTech EGT-8 CAN (model A)
FuelTech EGT-8 CAN (model B)
FuelTech EGT-4 CAN (model A)
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Reserved
Reserved
Reserved
Reserved
Reserved
Reserved
Reserved
-----
-----
-----
-----
-----
-----
-----
0x0920
0x0940
0x0960
0x0980
0x09A0
0x09C0
0x09E0
0x0920
0x0940
0x0960
0x0980
0x09A0
0x09C0
0x09E0
FuelTech EGT-4 CAN (model B)
FuelTech EGT-4 CAN (model C)
FuelTech EGT-4 CAN (model D)
Reserved for Future Use
Reserved for Future Use
Reserved for Future Use
Reserved for Future Use
Example: A FT500 device with the unique value of 3 will have the following ProductID:
(0x0280 << 5) + 3 = 0x5003
Where 0x0280 is the ProductTypeID for FT500 and 3 is the unique value. The “<<” is the
C language command rotate bit left, 0x0280 << 5 is the same as multiply 0x0280 with
0x0020.
MessageID’s list
• 0x0FF, 0x1FF, 0x2FF e 0x3FF – Real time reading broadcast
0x0FF – Critical priority
0x1FF – High priority
0x2FF – Medium priority
0x3FF – Low priority
Those are the MessageIDs that the FuelTech’s device will use to transmit its real time
readings. The rate for each broadcast will depend on the type of data, critical data will be
broadcasted more often. Examples of critical data: Ignition Cut, Two Step signal,
emergency signals, etc. Examples of high priority data: RPM, ignition timing, actual
injection flow, MAP, TPS, etc.
Values are always transmitted as signed 16 bits in big-endian byte order.
Statuses are transmitted as big-endian unsigned 16 bits.
Each real time data will be composed of 4 bytes:
REAL TIME DATA
0-1
Data identifier
(MeasureID)
10
2-3
Value or status
(big endian)
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
If a device needs to broadcast more than one reading at the same time it can do so using
a segmented packet:
Segmented packet PAYLOAD
MEASURE 1
MEASURE 2
MEASURE 3
0-1
2-3
4-5
6-7
8-9
10-11
MeasureID Value/Stat MeasureID Value/Stat MeasureID Value/Stat
The maximum number of measures that can be transmitted on segmented packages are:
1776/4 = 444
Another possibility is to use a CAN standard data frame to transmit 2 measures at a time,
all the devices in the CAN bus must be capable of receiving data using all the data layouts.
Standard packet PAYLOAD
MEASURE 1
MEASURE 2
0-1
2-3
4-5
6-7
MeasureID
Value
MeasureID
Value
A list with the available MeasureIDs is presented further in this document.
• 0x600 ~ 0x608 – Real time simple broadcast
Those are the MessageIDs that the FuelTech’s device will use to transmit its real time
readings using a fixed set of MeasureIDs. Each measure value is prefixed in a specific
position in payload. The rate for each broadcast is 100Hz.
Values are always transmitted as signed 16 bits in big-endian byte order.
The data is transmitted always using a CAN standard data frame (DataFieldID 0x00) to
transmit 4 measures at a time as shown in the following image:
Standard packet PAYLOAD
MEASURE 1 MEASURE 2 MEASURE 3 MEASURE 4
0-1
2-3
4-5
6-7
Value
Value
Value
Value
11
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
MeasureIDs
The least significant bit of the MeasureID is used to indicate if the following value is the
actual value or the reading status. Considering that the MeasureID have 16 bits in total
we will use 15 bits to identify the data that is being transmitted.
Bits 15 to 1
Data identifier
(DataID)
12
MeasureID
Bit 0
0: Data value
1: Data status
MeasureIDDataIDDescriptionUnityMultiplierBroadcast source
(rate*)
0x0000
0x0002
0x0004
0x0006
0x0008
0x000A
0x000C
0x000E0x0000
0x0001
0x0002
0x0003
0x0004
0x0005
0x0006
0x0007-
%
Bar
°C
°C
Bar
Bar
Bar-
0.1
0.001
0.1
0.1
0.001
0.001
0.001-
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
0x00100x0008-Note 1PowerFT ECU 100Hz
0x00120x0009Unknown
TPS
MAP
Air temperature
Engine temperature
Oil pressure
Fuel pressure
Water pressure
ECU Launch Mode (2-Step, 3-Step, Burnout,
Burnout + Spool)
ECU Batery voltageVolts0.010x00140x000ATraction speedKm/h1PowerFT ECU 100Hz
PowerFT ECU 100Hz
0x00160x000BDrag speedKm/h10x0018
0x001A
0x001C
0x001E
0x00200x000C
0x000D
0x000E
0x000F
0x0010Left front wheel speed
Right front wheel speed
Left rear wheel speed
Right rear wheel speed
Driveshaft RPMKm/h
Km/h
Km/h
Km/h
RPM1
1
1
1
10x00220x0011Gear-Note 20x00240x0012Disabled O2ƛ0.001
0x0026
0x00270x0013Cylinder 1 O2ƛ0.001
0x0028
0x00290x0014Cylinder 2 O2ƛ0.001
Brasil
www.FuelTech.com.br
+55(51)3019-0500
Gear Controller 100Hz
PowerFT ECU 100Hz
Gear Controller 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
Gear Controller 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
13
0x002A
0x002B0x0015Cylinder 3 O2ƛ0.001
0x002C
0x002D0x0016Cylinder 4 O2ƛ0.001
0x002E
0x002F0x0017Cylinder 5 O2ƛ0.001
0x0030
0x00310x0018Cylinder 6 O2ƛ0.001
0x0032
0x00330x0019Cylinder 7 O2ƛ0.001
0x0034
0x00350x001ACylinder 8 O2ƛ0.001
0x0036
0x00370x001BCylinder 9 O2ƛ0.001
0x0038
0x00390x001CCylinder 10 O2ƛ0.001
0x003A
0x003B0x001DCylinder 11 O2ƛ0.001
0x003C
0x003D0x001ECylinder 12 O2ƛ0.001
0x003E
0x003F0x001FCylinder 13 O2ƛ0.001
0x0040
0x00410x0020Cylinder 14 O2ƛ0.001
0x0042
0x00430x0021Cylinder 15 O2ƛ0.001
Brasil
www.FuelTech.com.br
+55(51)3019-0500
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
14
0x0044
0x00450x0022Cylinder 16 O2ƛ0.001
0x0046
0x00470x0023Cylinder 17 O2ƛ0.001
0x0048
0x00490x0024Cylinder 18 O2ƛ0.001
0x004A
0x004B0x0025Left bank O2ƛ0.001
0x004C
0x004D0x0026Right bank O2ƛ0.001
0x004E
0x004F0x0027Exhaust O2ƛ0.001
0x0050
0x0052
0x0054
0x0056
0x0058
0x005A
0x005C
0x005E
0x0060
0x0062
0x0064
0x0066
0x0068
0x006A
0x006C
0x006E
0x0070
0x0072
0x0074
0x0076
0x00780x0028
0x0029
0x002A
0x002B
0x002C
0x002D
0x002E
0x002F
0x0030
0x0031
0x0032
0x0033
0x0034
0x0035
0x0036
0x0037
0x0038
0x0039
0x003A
0x003B
0x003CDisabled EGT
Cylinder 1 EGT
Cylinder 2 EGT
Cylinder 3 EGT
Cylinder 4 EGT
Cylinder 5 EGT
Cylinder 6 EGT
Cylinder 7 EGT
Cylinder 8 EGT
Cylinder 9 EGT
Cylinder 10 EGT
Cylinder 11 EGT
Cylinder 12 EGT
Cylinder 13 EGT
Cylinder 14 EGT
Cylinder 15 EGT
Cylinder 16 EGT
Cylinder 17 EGT
Cylinder 18 EGT
Left bank EGT
Right bank EGT°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
Brasil
www.FuelTech.com.br
+55(51)3019-0500
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
PowerFT ECU 100Hz
WBO2 Nano 100Hz
WBO2 Slim 100Hz
Alcohol O2 100Hz
---
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
15
0x007A
0x007C
0x007E
0x0080
0x0082
0x0084
0x0086
0x0088
0x008A
0x008C
0x008E0x003D
0x003E
0x003F
0x0040
0x0041
0x0042
0x0043
0x0044
0x0045
0x0046
0x0047Exhaust EGT
ECU O2 Sensor Unit
ECU Speed Sensor Unit
ECU Pressure Sensor Unit
ECU Temperature Sensor Unit
ECU RPM
ECU Injection Bank A Time
ECU Injection Bank B Time
ECU Injection Bank A Duty Cycle
ECU Injection Bank B Duty Cycle
ECU Ignition Advance/Retard
°C
-
-
-
-
RPM
ms
ms
%
%
°0.1
Note 3
Note 4
Note 5
Note 6
1
0.01
0.01
0.1
0.1
0.1
0x00900x00482-Step Signal-Note 7
0x0092
0x0094
0x0096
0x0098
0x009A
0x009C
0x009E0x0049
0x004A
0x004B
0x004C
0x004D
0x004E
0x004F3-Step Signal
Burnout Signal
ECU Cut
ECU Air Conditioning
ECU Eletro Fan
GEAR Cut
GEAR Retard-
-
%
-
-
%
°Note 7
Note 7
1
Note 7
Note 7
1
0.1
0x00A00x0050GEAR Sensor VoltageVolts0.001
0x00A2
0x00A4
0x00A6
0x00A8
0x00AA
0x00AC
0x00AE
0x00B0
0x00B2
0x00B4
0x00B6
0x00B8
0x00BA
0x00BC
0x00BE
0x00C0
0x00C2
0x00C4
0x00C6
0x00C8
0x00CA
0x00CC0x0051
0x0052
0x0053
0x0054
0x0055
0x0056
0x0057
0x0058
0x0059
0x005A
0x005B
0x005C
0x005D
0x005E
0x005F
0x0060
0x0061
0x0062
0x0063
0x0064
0x0065
0x0066ECU Average O2
External Ignition output 1 discharge time
External Ignition output 2 discharge time
External Ignition output 3 discharge time
External Ignition output 4 discharge time
External Ignition output 5 discharge time
External Ignition output 6 discharge time
External Ignition output 7 discharge time
External Ignition output 8 discharge time
External Ignition output 9 discharge time
External Ignition output 10 discharge time
External Ignition output 11 discharge time
External Ignition output 12 discharge time
External Ignition output 13 discharge time
External Ignition output 14 discharge time
External Ignition output 15 discharge time
External Ignition output 16 discharge time
External Ignition Power Supply
External Ignition Power Supply Drop
External Ignition Power Level
External Ignition Temperature
External Ignition Capacitor 1 chargeƛ
uS
uS
uS
uS
uS
uS
uS
uS
uS
uS
uS
uS
uS
uS
uS
uS
V
V
mJ
°C
V0.001
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
.001
.001
1
0.1
0.1
Brasil
www.FuelTech.com.br
+55(51)3019-0500
PowerFT ECU 100Hz
PowerFT ECU 0.5Hz
PowerFT ECU 0.5Hz
PowerFT ECU 05.Hz
PowerFT ECU 05.Hz
PowerFT ECU 1KHz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 1KHz
PowerFT ECU 1KHz
Gear Controller 1KHz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
Gear Controller 500Hz
Gear Controller 500Hz
Gear Controller 100Hz
PowerFT ECU 100Hz
PowerFT ECU 100Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
0x00CE
0x00D0
0x00D2
0x00D4
0x00D6
0x00D8
0x00DA
0x00DC
0x00DE
0x00E0
0x00E2
0x00E4
0x00E6
0x00E8
0x00EA
0x00EC
0x00EE
0x00F0
0x00F2
0x00F4
0x00F6
0x00F8
0x00FA
0x00FC
0x00FE
0x0100
0x0102
0x0104
0x0106
0x0108
0x010A
0x010C
0x010E
0x0110
0x0112
0x0114
0x0116
0x0118
0x011A
0x011C
0x011E
0x0120
0x0122
0x0124
16
0x0067
0x0068
0x0069
0x006A
0x006B
0x006C
0x006D
0x006E
0x006F
0x0070
0x0071
0x0072
0x0073
0x0074
0x0075
0x0076
0x0077
0x0078
0x0079
0x007A
0x007B
0x007C
0x007D
0x007E
0x007F
0x0080
0x0081
0x0082
0x0083
0x0084
0x0085
0x0086
0x0087
0x0088
0x0089
0x008A
0x008B
0x008C
0x008D
0x008E
0x008F
0x0090
0x0091
0x0092
External Ignition Capacitor 2 charge
External Ignition Capacitor 3 charge
External Ignition Capacitor 4 charge
External Ignition Capacitor 1 charge time
External Ignition Capacitor 2 charge time
External Ignition Capacitor 3 charge time
External Ignition Capacitor 4 charge time
External Ignition Error code
External Ignition no load outputs
External Ignition partial discharge outputs
External Ignition damaged outputs
External Ignition disabled outputs
External Ignition operation status
Power level config for external ignition
Air conditioning button state
Two step button state
Three step button state
Transbreak button state
Burnout button state
ProNitrous button state
Progressive Nitrous #1 button state
Datalogger button state
Day/Night button state
Dashboard button state
Engine start button state
Generic PWM output increase button state
Gear upshift button state
Boost controller increase button state
Gear reset button state
Adjust change button
Adjust 1 button
Adjust 2 button
Adjust 3 button
Adjust 4 button
Adjust 5 button
Transmission temperature
Intercooler temperature
Oil temperature
PitLimit Switch/Button
Active Traction Control: enable switch
Active Traction Control: table 1 button
Active Traction Control: table 2 button
Active Traction Control: table 3 button
Active Traction Control: table 4 button
V
V
V
uS
uS
uS
uS
-
-
-
-
-
-
mJ
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
°C
°C
°C
-
-
-
-
-
-
Brasil
www.FuelTech.com.br
+55(51)3019-0500
0.1
0.1
0.1
1
1
1
1
Note 8
Note 9
Note 9
Note 9
Note 9
Note 10
1
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
0.1
0.1
0.1
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
Internal use only
Internal use only
Internal use only
Internal use only
PowerFT ECU 10Hz
Internal use only
Internal use only
PowerFT ECU 10Hz
Internal use only
PowerFT ECU 10Hz
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
PowerFT ECU 10Hz
Internal use only
PowerFT ECU 10Hz
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
0x0126
0x0128
0x012A
0x012C
0x012E
0x0130
0x0132
0x0134
0x0136
0x0138
0x013A
0x013C
0x013E
0x0140
0x0142
0x0144
0x0146
0x0224
0x0226
0x0228
0x022A
0x022C
0x022E
0x0230
0x0232
0x0234
0x0236
0x0238
0x023A
0x023C
0x023E
0x0240
0x0242
0x0244
0x0246
0x0248
0x024A
0x024C
0x024E
0x0250
0x0252
0x0254
0x0256
0x0258
17
0x0093
0x0094
0x0095
0x0096
0x0097
0x0098
0x0099
0x009A
0x009B
0x009C
0x009D
0x009E
0x009F
0x00A0
0x00A1
0x00A2
0x00A3
0x0112
0x0113
0x0114
0x0115
0x0116
0x0117
0x0118
0x0119
0x011A
0x011B
0x011C
0x011D
0x011E
0x011F
0x0120
0x0121
0x0122
0x0123
0x0124
0x0125
0x0126
0x0127
0x0128
0x0129
0x012A
0x012B
0x012C
Active Traction Control: table 5 button
Active Traction Control: table 6 button
Active Traction Control: next table button
Active Traction Control: previous table button
Tire temperature: Front Left
Tire temperature: Front Right
Tire temperature: Rear Left
Tire temperature: Rear Right
Track temperature
Generic Input: button 1
Generic Input: button 2
Generic Input: button 3
Generic Input: button 4
Generic Input: button 5
Generic Input: button 6
Generic Input: button 7
Generic Input: button 8
Left turn signal
Right turn signal
Low beam
High beam
External Ignition Switch voltage
External Ignition CPU supply voltage
External Ignition CPU temperature
External Ignition operation time
MFI external switch
Progressive Nitrous #2 button state
Gear Reverse button
Gear Drive button
Blip signal
Bank A Injector 1 Duty cycle
Bank A Injector 2 Duty cycle
Bank A Injector 3 Duty cycle
Bank A Injector 4 Duty cycle
Bank A Injector 5 Duty cycle
Bank A Injector 6 Duty cycle
Bank A Injector 7 Duty cycle
Bank A Injector 8 Duty cycle
Bank A Injector 9 Duty cycle
Bank A Injector 10 Duty cycle
Bank A Injector 11 Duty cycle
Bank A Injector 12 Duty cycle
Bank B Injector 1 Duty cycle
Bank B Injector 2 Duty cycle
-
-
-
-
°C
°C
°C
°C
°C
-
-
-
-
-
-
-
-
-
-
-
-
V
V
°C
S
-
-
-
-
-
%
%
%
%
%
%
%
%
%
%
%
%
%
%
Brasil
www.FuelTech.com.br
+55(51)3019-0500
Note 7
Note 7
Note 7
Note 7
0.1
0.1
0.1
0.1
0.1
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
Note 7
0.001
0.001
0.1
0.1
Note 7
Note 7
Note 7
Note 7
Note 7
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 10Hz
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
0x025A
0x025C
0x025E
0x0260
0x0262
0x0264
0x0266
0x0268
0x026A
0x026C
0x026E
0x0270
0x0272
0x0274
0x0276
0x0278
0x027A
0x027C
0x027E
0x0280
0x0282
0x0284
0x0286
0x0288
0x028A
0x028C
0x028E
0x0290
0x0292
0x0294
0x0296
0x0298
0x029A
0x029C
0x029E
0x02A0
0x02A2
0x02A4
0x02A6
0x02A8
0x02AA
0x02AC
0x02AE
0x02B0
18
0x012D
0x012E
0x012F
0x0130
0x0131
0x0132
0x0133
0x0134
0x0135
0x0136
0x0137
0x0138
0x0139
0x013A
0x013B
0x013C
0x013D
0x013E
0x013F
0x0140
0x0141
0x0142
0x0143
0x0144
0x0145
0x0146
0x0147
0x0148
0x0149
0x014A
0x014B
0x014C
0x014D
0x014E
0x014F
0x0150
0x0151
0x0152
0x0153
0x0154
0x0155
0x0156
0x0157
0x0158
Bank B Injector 3 Duty cycle
Bank B Injector 4 Duty cycle
Bank B Injector 5 Duty cycle
Bank B Injector 6 Duty cycle
Bank B Injector 7 Duty cycle
Bank B Injector 8 Duty cycle
Bank B Injector 9 Duty cycle
Bank B Injector 10 Duty cycle
Bank B Injector 11 Duty cycle
Bank B Injector 12 Duty cycle
Gear downshift button state
EV Battery temperature
EV Battery Voltage
EV Battery Current
EV Battery Charge
EV Motor 1 RPM
EV Motor 1 Current
EV Motor 1 Voltage
EV Motor 1 Torque
EV Motor 1 Temperature
EV Motor 2 RPM
EV Motor 2 Current
EV Motor 2 Voltage
EV Motor 2 Torque
EV Motor 2 Temperature
EV Inverter 1 Temperature
EV Inverter 2 Temperature
Park button
Neutral button
Self Dial
Opponent Dial
Bump up button
Bump down button
Super bump button
Multi-function button
Total Fuel Flow
Brake pressure
Generic outputs state
Day/Nigth state
External Ignition Power Supply – B
External Ignition Power Supply Drop - B
External Ignition Power Level – B
External Ignition Temperature - B
External Ignition Capacitor 1 charge - B
%
%
%
%
%
%
%
%
%
%
-
°C
V
A
%
RPM
A
V
%
°C
RPM
A
V
%
°C
°C
°C
-
-
S
S
-
-
-
-
L/min
Bar
-
V
V
mJ
°C
V
Brasil
www.FuelTech.com.br
+55(51)3019-0500
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
Note 7
0.1
1
1
1
1
1
1
1
0.1
1
1
1
1
0.1
0.1
0.1
Note 7
Note 7
0.001
0.001
Note 7
Note 7
Note 7
Note 7
0.01
0.001
Note 9
Note 12
.001
.001
1
0.1
0.1
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
Internal use only
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
Internal use only
Internal use only
PowerFT ECU 0.5Hz
Internal use only
Internal use only
Internal use only
Internal use only
Internal use only
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
0x02B2
0x02B4
0x02B6
0x02B8
0x02BA
0x02BC
0x02BE
0x02C0
0x02C2
0x02C4
0x02C6
0x02C8
0x02CA
0x02CC
0x02CE
0x02D0
0x02D2
0x02E0
0x02E2
0x02E4
0x02E6
0x02E8
0x02EA
0x02EC
0x02EE
0x02F0
0x02F2
0x02F4
0x02F6
0x02F8
0x02FA
0x02FC
0x02FE
0x0300
0x0302
0x0304
0x0306
0x0308
0x030A
0x030C
0x030E
0x0310
0x0312
0x0314
19
0x0159
0x015A
0x015B
0x015C
0x015D
0x015E
0x015F
0x0160
0x0161
0x0162
0x0163
0x0164
0x0165
0x0166
0x0167
0x0168
0x0169
0x0170
0x0171
0x0172
0x0173
0x0174
0x0175
0x0176
0x0177
0x0178
0x0179
0x017A
0x017B
0x017C
0x017D
0x017E
0x017F
0x0180
0x0181
0x0182
0x0183
0x0184
0x0185
0x0186
0x0187
0x0188
0x0189
0x018A
External Ignition Capacitor 2 charge – B
External Ignition Capacitor 3 charge – B
External Ignition Capacitor 4 charge – B
External Ignition Capacitor 1 charge time – B
External Ignition Capacitor 2 charge time – B
External Ignition Capacitor 3 charge time – B
External Ignition Capacitor 4 charge time - B
External Ignition Error code – B
External Ignition no load outputs – B
External Ignition partial discharge outputs – B
External Ignition damaged outputs – B
External Ignition disabled outputs – B
External Ignition operation status – B
External Ignition Switch voltage – B
External Ignition CPU supply voltage – B
External Ignition CPU temperature – B
External Ignition operation time – B
Ride Height
Shock Sensor FR (Front Right)
Shock Sensor FL (Front Left)
Shock Sensor RR (Rear Right)
Shock Sensor RL (Rear Left)
TwoStep Clutch Button
Brake Switch
Back Pressure
DiffCtrl_SelPosition_1
DiffCtrl_SelPosition_2
DiffCtrl_EngPosition_1
DiffCtrl_EngPosition_2
DiffCtrl_EngPosition_3
Yaw Rate
Actual Gear Pulse
Clutch Pressure
Nitro Pressure
Nitro Pressure 2
Transmission Pressure
Westgate Pressure Input
Pan Vaccun
Torque Convert Pressure
Lambda Narrow
Boost 1 RPM
Boost 2 RPM
Inputshaft RPM
Input Expander Bat
V
V
V
uS
uS
uS
uS
-
-
-
-
-
-
V
V
°C
S
-
-
-
-
-
-
-
Bar
-
-
-
-
-
-
-
Bar
Bar
Bar
Bar
-
-
-
-
RPM
RPM
RPM
V
Brasil
www.FuelTech.com.br
+55(51)3019-0500
0.1
0.1
0.1
1
1
1
1
Note 8
Note 9
Note 9
Note 9
Note 9
Note 10
0.001
0.001
0.1
0.1
-
0.001
0.001
0.001
0.001
Note 1
Note 7
0.001
-
-
-
-
-
-
-
0.001
-
-
0.001
-
-
-
Note 3
-
-
-
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 50Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 25Hz
FTSPARK 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
Internal use only
Internal use only
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
0x0316
0x0318
0x031A
0x031C
0x031E
0x0320
0x0322
0x0324
0x0326
0x0328
0x032A
0x032C
0x032E
0x0330
0x0332
0x0334
0x0336
0x0338
0x033A
0x033C
0x033E
0x0340
0x0342
0x0344
0x0346
0x0348
0x034A
0x034C
0x034E
0x0350
0x0352
0x0354
0x0356
0x0358
0x035A
0x035C
0x035E
0x0360
0x0362
0x0364
0x0366
0x0368
0x036A
0x036C
20
0x018B
0x018C
0x018D
0x018E
0x018F
0x0190
0x0191
0x0192
0x0193
0x0194
0x0195
0x0196
0x0197
0x0198
0x0199
0x019A
0x019B
0x019C
0x019D
0x019E
0x019F
0x01A0
0x01A1
0x01A2
0x01A3
0x01A4
0x01A5
0x01A6
0x01A7
0x01A8
0x01A9
0x01AA
0x01AB
0x01AC
0x01AD
0x01AE
0x01AF
0x01B0
0x01B1
0x01B2
0x01B3
0x01B4
0x01B5
0x01B6
Input Expander Sensor 5V
Input Expander Temperature
Input Expander Status
P2P Switch
Westgate 2 BoostP Button
Westgate 2 Pressure Input
ALS Button Input
Interlock Input
Upshift Request
Upshift Validated
Downshift Request
Downshift Validated
Flow Pump A
Flow Pump B
Flow Return A
Flow Return B
EGate 1 Temperature
EGate 2 Temperature
EGate BoostP Button
Peak and Hold Status M1
Peak and Hold Status M2
Peak and Hold Driver 1 Status M1
Peak and Hold Driver 2 Status M1
Peak and Hold Driver 3 Status M1
Peak and Hold Driver 4 Status M1
Peak and Hold Driver 5 Status M1
Peak and Hold Driver 6 Status M1
Peak and Hold Driver 7 Status M1
Peak and Hold Driver 8 Status M1
Peak and Hold Driver 1 Status M2
Peak and Hold Driver 2 Status M2
Peak and Hold Driver 3 Status M2
Peak and Hold Driver 4 Status M2
Peak and Hold Driver 5 Status M2
Peak and Hold Driver 6 Status M2
Peak and Hold Driver 7 Status M2
Peak and Hold Driver 8 Status M2
RPM CAN
Lockup On Button
Lockup Off Button
Fuel Total Consumption
Fuel Total Consumption Reset Button
Bracket Pre Staging Button
Throttle Stop Bump Down Button
V
°C
-
-
-
-
-
-
-
-
-
-
-
-
-
-
°C
°C
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
RPM
-
-
L
-
-
-
Brasil
www.FuelTech.com.br
+55(51)3019-0500
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
-
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
FT_PnH Pro
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
0x036E
0x0370
0x0386
0x0388
0x038A
0x038C
0x038E
0x0390
0x0408
0x040A
0x046A
0x046C
0x046E
0x0470
0x0472
0x0474
0x0476
0x0478
0x047A
0x047C
0x047E
0x0480
0x0482
0x0484
0x0486
0x0488
0x048A
0x048C
0x048E
0x0490
0x0492
0x0494
0x0496
0x04980x01B7
0x01B8
0x01C3
0x01C4
0x01C5
0x01C6
0x01C7
0x01C8
0x0204
0x0205
0x0235
0x0236
0x0237
0x0238
0x0239
0x023A
0x023B
0x023C
0x023D
0x023E
0x023F
0x0240
0x0241
0x0242
0x0243
0x0244
0x0245
0x0246
0x0247
0x0248
0x0249
0x024A
0x024B
0x024CThrottle Stop Bump Up Button
Throttle Stop Super Bump Button
EV Battery DCL
EV Battery CCL
EV Battery Lowest Cell Voltage
EV Battery Highest Cell Voltage
EV Battery Lowest Cell Temperature
EV Battery Highest Cell Temperature
EV Torque Target
EV Regen Target
Tire pressure 1
Tire pressure 2
Tire pressure 3
Tire pressure 4
Tire pressure 5
Tire pressure 6
Tire pressure 7
Tire pressure 8
Tire pressure 9
Tire pressure 10
Tire pressure 11
Tire pressure 12
Tire temperature 1
Tire temperature 2
Tire temperature 3
Tire temperature 4
Tire temperature 5
Tire temperature 6
Tire temperature 7
Tire temperature 8
Tire temperature 9
Tire temperature 10
Tire temperature 11
Tire temperature 12
0xFFFE
0xFFFF0x7FFFLast DataID
-
-
A
A
V
V
°C
°C
%
%
Bar
Bar
Bar
Bar
Bar
Bar
Bar
Bar
Bar
Bar
Bar
Bar
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
°C
-
-
1
1
1
1
0.1
0.1
1
1
0.001
0.001
0.001
0.001
0.001
0.001
0.001
0.001
0.001
0.001
0.001
0.001
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
PowerFT ECU 10Hz
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
TPMS reader
Only one of the possible sources is allowed to broadcast a specific DataID on the network.
If one or more sources are broadcasting the same DataID a network conflict state is raised.
21
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
*The broadcast transmission rate may vary when the ECU is under high RPM
Note 1
Value 0: None (running)
Value 1: Burnout
Value 2: Burnout Spool (Burnout and 2-Step)
Value 3: 3-Step
Value 4: 2-Step
Note 2
Value -2: Park
Value -1: Reverse
Value 0: Neutral
Value 1: First gear
Value 2: Second gear
Value 3: Third gear
Value 4: Fourth gear
Value 5: Fifth gear
Value 6: Sixth gear
Value 7: Seventh gear
Value 8: Eighth gear
Value 9: Ninth gear
Value 10: Tenth gear
Note 3
Value 0: Undefined
Value 1: Lambda
Value 2: AFR methanol
Value 3: AFR ethanol
Value 4: AFR gasoline
Value 0xFF: Undefined
Note 4
Value 0: Km/h
Value 1: Mph
Note 5
Value 0: bar
Value 1: PSI
22
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Value 2: KPa
Note 6
Value 0: °C
Value 1: °F
Note 7
Value 0: Off
Value 1: On
Note 8
Bit 0: Unknown pulse width received by the FT Ignition Bus.
Bit 1: Incorrect ignition order in semi-sequential operation.
Bit 2: Over voltage in the high voltage bus. (external ignition disabled until next power
cicle).
Bit 3: Under voltage in the output drivers power supply. (external ignition disabled while
condition exists).
Bit 4: Charge circuit unable to charge capacitors.
Bit 5: Power supply under voltage.
Bit 6: 12V switch under voltage.
Note 9
Bit 0: Output 1
Bit 1: Output 2
Bit 2: Output 3
Bit 3: Output 4
Bit 4: Output 5
Bit 5: Output 6
Bit 6: Output 7
Bit 7: Output 8
Bit 8: Output 9
Bit 9: Output 10
Bit 10: Output 11
Bit 11: Output 12
Bit 12: Output 13
Bit 13: Output 14
Bit 14: Output 15
Bit 15: Output 16
Note 10
23
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Bit 0: Internal use
Bit 1: Internal use
Bit 2: High power mode enabled
Note 11
Incremental counter of errors in the respective cylinder
Note 12
Value 0: Day
Value 1: Nigth
24
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Simplified packets
In addition to the standard packets the FTCAN 2.0 can also be used in conjunction with
simplified broadcast packets. This simplified broadcast packets have a fixed and defined
data structure and are only broadcasted by the ECUs. The following table shows the
simplified packets:
Bytes
ID (FT500)ID (FT600/550/450)
1
2
3
4
5
6
0x140006000x14080600TPSMAP0x140006010x14080601Oil PressureFuel PressureWater PressureGear
0x140006020x14080602Exhaust O2RPMOil TemperaturePit Limit
0x140006030x14080603Wheel Speed FRWheel Speed FLWheel Speed RRWheel Speed RL
0x140006040x14080604Traction Ctrl - SlipTraction Ctrl - RetardTraction Ctrl - CutHeading
0x140006050x14080605Shock Sensor FRShock Sensor FLShock Sensor RRShock Sensor RL
0x140006060x14080606G-force (accel)G-force (lateral)Yaw-rate (frontal)Yaw-rate (lateral)
0x140006070x14080607Lambda CorrectionInj Time Bank AInj Time Bank B
0x140006080x14080608Oil TemperatureFuel Flow Total
Transmission
TemperatureFuel ConsumptionBrake Pressure
Air Temperature
7
8
Engine Temperature
The data format, unit and multipliers are the same used in the standard packets.
Simplified packets - EGT-4
Temperature data format and conversion
• Channel temperature values are transmitted as signed 16 bits in big-endian byte
order.
• Temperature resolution: 0.125°C / bit
• Data conversion:
o Temperature value (°C) = Channel bytes * 0.125
o Maximum temperature: 1000°C (0x1F40 on channel bytes)
o Minimum temperature: -50°C (0xFE70 on channel bytes)
o Examples:
 1°C equals value 8 (0x0008)
 500°C equals value 4000 (0x0FA0)
 -10°C equals value -80 (0xFFB0)
• When an error is detected on a channel (eg. thermocouple disconnected) the EGT-4
will broadcast a reading of 1050°C (0x20D0).
25
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Bytes
ID (EGT-4)
Model A0x02400000
Model B0x02480000
Model C0x02500000
Model D0x02580000
0
1
Channel 1
2
3
Channel 2
4
Channel 3
5
6
7
Channel 4
Simplified packets – SwitchPanel
ID: 0x12200320 – SW-8 Button State
ID: 0x12200321 – SW-8 Button Color
ID: 0x12218320 – SW-8 mini Button State
ID: 0x12218321 – SW-8 mini Button Color
ID: 0x12210320 – SW-5 mini Button State
ID: 0x12210321 – SW-5 mini Button Color
ID: 0x12208320 – SW-5 mini Button State
ID: 0x12208321 – SW-5 mini Button Color
Length: 8 Bytes
Messages transmitted by the switchpanel every 250 ms or on change (50 ms minimum)
•
Byte 0 (of 7): 0xFF
•
Byte 1: 0xFF
•
Byte 2 o Bit 0: Button 1 State (0 = not pressed, 1 = pressed)
Bit 1: Button 2 State
Bit 2: Button 3 State
Bit 3: Button 4 State
Bit 4 for Bit 7: Set to 0, not used
•
Byte 3 o Bit 0: Button 5 State (0 = not pressed, 1 = pressed)
Bit 1: Button 6 State
Bit 2: Button 7 State
Bit 3: Button 8 State
Bit 4 for Bit 7: Set to 0, not used
•
•
•
•
26
Byte 4: 0x00
Byte 5: 0x00
Byte 6: 0x00
Byte 7: 0x00
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Connector Pinout
• PowerFT ECUs
Frontal view of the connector on the back of the ECU
27
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Examples
Example 1: Standard CAN layout – Single packet with RPM value
28
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Example 2: Standard CAN layout – Single packet with RPM and TPS values
29
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Example 3: FTCAN layout - Single packet with RPM value
30
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Example 4: FTCAN layout - Multiple packets with 5 different values
31
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
Example 5: FTCAN layout EGT-4 - Single packet with Temperature value
32
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835FTCAN 2.0 protocol
FTCAN2.0 segmented packet flowchart
33
Brasil
www.FuelTech.com.br
+55(51)3019-0500
International
www.FuelTech.net
+1(678)493-3835