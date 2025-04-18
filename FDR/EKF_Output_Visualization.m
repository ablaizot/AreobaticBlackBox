clear
clc

%% Output Visualization for EKF Position/Velocity Data
%David Moody
%Project 137 Aerobatic Black Box
%2025-04-15

%% Load .bin Log File

filename = 'replay-00000062.BIN';
bin = ardupilotreader(filename);
msg = readMessages(bin);

%% Read messages in chosen time interval [d1 d2]

d1 = duration([0 0 1100],'Format','hh:mm:ss.SSSSSS');
d2 = d1 + duration([0 0 1200],'Format','hh:mm:ss.SSSSSS');
%attMsg = readMessages(bin,'MessageName',{'ATT'},'Time',[d1 d2]);

%% Optional Debugging: Read parameters and error logs

%params = readParameters(bin);
%log = readLoggedOutput(bin);

%% Extract EKF Output

%All relevant EKF/Replay data
XKFMsg = readMessages(bin,'MessageName',{'XKF1'},'Time',[d1 d2]);

%Seperate each EKF/Replay instance
EKF_0 = XKFMsg.MsgData{1,1};
EKF_1 = XKFMsg.MsgData{2,1};
Replay_100 = XKFMsg.MsgData{3,1};
Replay_101 = XKFMsg.MsgData{4,1};

%% Extract ORGN and POS Data

%Origin for EKF North East Down Coordinates
OrgMsg = readMessages(bin,'MessageName',{'ORGN'},'Time',[d1 d2]);
OrgData_0 = OrgMsg.MsgData{1,1};


%Geodetic Position Data - Compare to EKF Output
POSMsg = readMessages(bin,'MessageName',{'POS'},'Time',[d1 d2]);

%% Convert EKF NED Position Data to Geodetic

%Relevant position information and components
Pos_0 = EKF_0{:, 10:12};
P_North = Pos_0(:, 1);
P_East = Pos_0(:, 2);
P_Down = Pos_0(:, 3);

%Relevant origin information and components
Org_0 = OrgData_0{:, 3:5};
Org_lat = Org_0(1,1);
Org_long = Org_0(1,2);
Org_h = Org_0(1,3);

%Convert NED position coordinates to geodetic using MATLAB function
[P_lat, P_long, P_h] = ned2geodetic(P_North, P_East, P_Down, Org_lat, Org_long, Org_h, referenceSphere('earth'));

%Convert height units from meters to feet
P_h = P_h*3.28084;

%% Vector for time in seconds

%A bit confused about this
%I think it's just in hours:minutes:seconds already with the way MATLAB formats the data?
%Even though according to Ardupilot documentation it should be in microseconds.
t_sec = seconds(EKF_0{:, 1});

%% EKF Orientation Data

Orient_0 = EKF_0{:, 3:5};
O_pitch = Orient_0(:, 2);
O_roll = Orient_0(:, 1);
O_heading = Orient_0(:, 3);


%% TODO: Add Control Inputs
%Placeholder for now

%Grab 2 nearest time values and do linear interpolation between them for
%each "frame" of the FDR

Aileron = zeros(length(P_h), 1);
Elevator = zeros(length(P_h), 1);
Rudder = zeros(length(P_h), 1);

%% Start date and time from GPS
%To make FDR replay start at time of the actual flight

%GPS Data Message
GPS_Data = readMessages(bin,'MessageName',{'GPS'},'Time',[d1 d2]);
GPS_Data = GPS_Data.MsgData{1,1};

%From Ardupilot data: GWk is weeks since Jan 6th 1980 at midnight
%GMS is milliseconds since start of GPS Week
GWk = GPS_Data{1, 5};
GMS = GPS_Data{1, 4};

%Define GPS start time
GPS_Epoch = datetime(1980, 1, 6, 0, 0, 0, 'TimeZone', 'UTC');

%Convert weeks and milliseconds to seconds since 1980
sec_Since_Epoch = GWk*7*24*3600 + (GMS/1000);

%Add to Epoch
Start_Time = GPS_Epoch + seconds(sec_Since_Epoch);

%Convert to string
Start_Time.Format = 'MM/dd/yyyy hh:mm:ss';
%Start_Time = datevec(Start_Time);

%D_Print = sprintf(['DATE,%d/%d/%d'], Start_Time)
%T_Print = 

%% Create FDR File

%FDR filename
filename = 'Test_FDR_4.fdr';
fileID = fopen(filename, 'w');

%Write setup/header text
fprintf(fileID, ['I\n' ...
    '2 Version\n' ...
    'ACFT,Aircraft/Laminar Research/Cirrus SF-50/CirrusSF50.acf\n' ...
    'TAIL,N12345,\n' ...
    'PRES,29.83,\n' ...
    'TEMP,65,\n' ...
    'WIND,230,0,\n' ...
    'CALI,-71.197,42.00,122\n' ...
    'WARN,1,aural_alarm.wav\n' ...
    'TEXT,20,Testing testing one two three.\n' ...
    'MARK,30,Testing text marker.\n' ...
    'EVNT,10,5\n\n']);

%Write start date and time time
%fprintf(fileID, );
%'DATE,04/16/2025,\n'


%Write data to FDR file
%See Google Document on XPlane FDR Format details
for n = 1:length(t_sec)
    fprintf(fileID, ['DATA,%f,0,%f,%f,%f,0,%f,%f,%f,%f,%f,%f,0,0,0,0,0,0,0,0,0,0,0,0,' ...
        '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0' ...
        ',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,' ...
        '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,\n\n'], ...
        t_sec(n), P_long(n), P_lat(n), P_h(n), Aileron(n), Elevator(n), ...
        Rudder(n), O_pitch(n), O_roll(n), O_heading(n));
end

%Close file
fclose(fileID);
