# this code is to generate an ideal SVC trace data
import os

print("Writing data to the file...")
with open('./video_trace/idealSVC_352_288_2.txt', 'w+') as f:
    for i in range(0, 500):
        f.write("8155\n")
        f.write("14337\n")
        f.write("29868\n")
        f.write("50484\n")
        f.write("71370\n")
        f.write("98574\n")
        f.write("128042\n")
        f.write("155904\n")
        # all in bit
print("Completed")