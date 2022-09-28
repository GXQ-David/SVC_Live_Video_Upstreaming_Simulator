import matplotlib.pyplot as plt

generate_time = []
next_time = []
sent_real = []
arrive_real = []
sent_ideal = []
arrive_ideal = []
sub_real = []
sub_ideal = []
sub = []
frame_time = 0.04    #seconds

for i in range(0, 150):
    generate_time.append(i * frame_time)
    next_time.append((i+1) * frame_time)

with open('./result/network_352_288.txt', 'rb') as f:
    for line in f:
        parse = line.split()
        sent_real.append(float(parse[0]))
        arrive_real.append(float(parse[1]))
f.close()

if len(arrive_real) == len(next_time):
    for i in range(len(next_time)):
        sub_real.append(arrive_real[i] - next_time[i])
        
with open('./result/network_352_288_i2.txt', 'rb') as f:
    for line in f:
        parse = line.split()
        sent_ideal.append(float(parse[0]))
        arrive_ideal.append(float(parse[1]))
f.close()

if len(arrive_ideal) == len(next_time):
    for i in range(len(next_time)):
        sub_ideal.append(arrive_ideal[i] - next_time[i])
        sub.append(sub_real[i] - sub_ideal[i])

#plt.bar(range(len(sub_real)), sub_real, label = 'Delay (real)')
#plt.bar(range(len(sub_ideal)), sub_ideal, label = 'Delay (ideal)')
plt.bar(range(len(sub)), sub, label = 'Difference')

plt.legend()
plt.xlabel('Frame')
plt.ylabel('Time (s)')
plt.title('Network Status')

plt.show()