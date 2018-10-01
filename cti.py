import csv
import os


os.rename('facts/constant_to_int.csv', 'facts/constant_to_int.csv.bak')

csv_in = open('facts/constant_to_int.csv.bak', 'rb')
csv_out = open('facts/constant_to_int.csv', 'wb')


writer = csv.writer(csv_out, delimiter='\t')
for row in csv.reader(csv_in, delimiter='\t'):
    number = row[1]
    if ((int(number) <=  9223372036854775807) & (int(number) >= -9223372036854775807)):
        writer.writerow(row)

csv_in.close()
csv_out.close()
