# celsius, %, hpa, ft, m, mm/s^2, mm/s^2, mm/s^2, deg, deg, deg, milliseconds

import pycstruct
import csv
import os

person = pycstruct.StructDef()
STRUCT_SIZE = 32

num = 0
while os.path.exists(f"data{num}.csv"):
    num += 1

person.add('float32', 'temp')
person.add('float32', 'hum')
person.add('float32', 'pres')
person.add('float32', 'alt')
person.add('int16', 'ax')
person.add('int16', 'ay')
person.add('int16', 'az')
person.add('int16', 'gx')
person.add('int16', 'gy')
person.add('int16', 'gz')
person.add('uint32', 't')

inbytes = []

with open('E:/data.bin', 'rb') as f:
    while True:
        data = f.read(STRUCT_SIZE)
        if not data:
            break  # End of file
        inbytes.append(person.deserialize(data))

with open(f"data{num}.csv", mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(inbytes[0].keys())

    num_rows = len(inbytes)
    
    # Write each row of data
    for i in range(num_rows):
        row = [inbytes[i][key] for key in inbytes[i]]
        writer.writerow(row)

