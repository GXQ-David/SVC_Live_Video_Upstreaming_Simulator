# this code is to extract video trace data from the output of the JSVM encoder
import os

with open('./video_trace/bus_8layers_352_288.txt', 'rb') as f:
    for line in f:
        data = line.split()
        print(int(data[-2]))