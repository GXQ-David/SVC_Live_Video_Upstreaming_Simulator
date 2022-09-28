import statistics

data = []
l1 = []
l2 = []
l3 = []
l4 = []
l5 = []
l6 = []
l7 = []
l8 = []

with open('./video_trace/bus_8layers_176_144.txt', 'rb') as f:
    data = f.readlines()
    for i in range(0, 150):
        l1.append(float(data[8*i]))
        l2.append(float(data[8*i+1]))
        l3.append(float(data[8*i+2]))
        l4.append(float(data[8*i+3]))
        l5.append(float(data[8*i+4]))
        l6.append(float(data[8*i+5]))
        l7.append(float(data[8*i+6]))
        l8.append(float(data[8*i+7]))

print(statistics.mean(l1))
print(statistics.mean(l2))
print(statistics.mean(l3))
print(statistics.mean(l4))
print(statistics.mean(l5))
print(statistics.mean(l6))
print(statistics.mean(l7))
print(statistics.mean(l8))