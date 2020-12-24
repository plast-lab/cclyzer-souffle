import csv
import os
import sys

folder=sys.argv[1]
if not(folder.endswith('/')):
    folder=folder+'/'
os.rename(folder+'constant_to_int.csv', folder+'constant_to_int.csv.bak')

csv_in = open(folder+'constant_to_int.csv.bak', 'r')
csv_out = open(folder+'constant_to_int.csv', 'w')


writer = csv.writer(csv_out, delimiter='\t')
for row in csv.reader(csv_in, delimiter='\t'):
    number = row[1]
    if ((int(number) <=  2147483647) & (int(number) >= -2147483647)):
        writer.writerow(row)

csv_in.close()
csv_out.close()
