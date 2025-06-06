load("..\11_8_24\00000011.log-9169881.mat")
figure
plot(GPS_0(:,4))
xlabel("Time (s)")
ylabel("GPS Status")

figure
plot(GPS_0(:,7))
xlabel("Time (s)")
ylabel("Number of Satellites")

% Remove data without lock
GPS_0(GPS_0(:,4) == 1, :) = [];

fdr_file = fopen('example_test_1.fdr', 'w');

fprintf(fdr_file, 'A\n2 This is the needed beginning of the file: A or I for Apple or IBM carriage-returns, followed by an IMMEDIATE carriage return, followed by the version number of 2\nCOMM, This is a sample FDR file, use it to generate your own Flight Data Recorder files. \nCOMM, Data entries are as seen in the FDR window in X-Plane \nCOMM, EVERY LINE BELOW (EXCEPT DATA) MUST END IN A COMMA!\nCOMM, WE USE COMMAS TO INDICATE END OF LINE IN THIS FILE, SINCE MANY SPREADHSEETS LIKE TO COMMA-DELIMIT.\nCOMM, of course, any line that starts with the letters COMM is a comment.\nCOMM, Go to https://www.x-plane.com/kb/fdr-files-x-plane-11/ for more info\n\nTAIL,N12345,\nDATE,08/10/2004,\nPRES,29.83,\nTEMP,65,\nWIND,230,16,\nTIME,18:00:00\nWARN, 5,Resources/sounds/alert/1000ft.WAV,\nTEXT, 5,This is a test of the spoken text.,\nMARK, 5,Marker at 5 seconds,\nMARK,15,Marker at 15 seconds,\nEVNT, 5,10,\nACFT,Aircraft/Laminar Research/Cessna 172SP/Cessna_172SP_G1000.acf\n\n');

time = GPS_0(:,2);
latitude = GPS_0(:,9);
longitude = GPS_0(:,10);

% Write the GPS data
for i = 1:length(time)
    fprintf(fdr_file, 'DATA, %d,15,%f,%f,4000, 0,0,0,0,0,1,0, 250,0,0,0,0.5, %d,0, 0,0,0,0,1,1,1,1,0, 11010,10930,4,4,90,270,0,0,10,10,1,1,10,10,0,0,0,0,10,10,0,0,0,0,0,0,0,0,0,0,500, 29.92,0,0,0,0,0,0 , 1,1,0,0 , 2000,2000,0,0 , 2000,2000,0,0 , 30,30,0,0 , 100,100,0,0 , 100,100,0,0 , 0,0,0,0 , 0,0,0,0 , 1500,1500,0,0 , 400,400,0,0 , 1000,1000,0,0 , 1000,1000,0,0 , 0,0,0,0,\n', i-1,latitude(i), longitude(i),i-1);
end