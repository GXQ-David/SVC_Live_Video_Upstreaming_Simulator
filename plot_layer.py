import matplotlib.pyplot as plt
import statistics

sub = []
total_real = []
sent_real = []
discard_real = []
with open('./result/layer_352_288.txt', 'rb') as f:
    for line in f:
        parse = line.split()
        total_real.append(float(parse[0]))
        sent_real.append(float(parse[1]))
        discard_real.append(float(parse[2]))
f.close()

total_ideal = []
sent_ideal = []
discard_ideal = []
with open('./result/layer_352_288_i2.txt', 'rb') as f:
    for line in f:
        parse = line.split()
        total_ideal.append(float(parse[0]))
        sent_ideal.append(float(parse[1]))
        discard_ideal.append(float(parse[2]))
f.close()

if len(sent_real) == len(sent_ideal):
    for i in range(len(sent_ideal)):
            sub.append(sent_real[i] - sent_ideal[i])

plt.plot(range(len(sent_real)), sent_real, '.-', label = 'real')
#plt.plot(range(len(sent_ideal)), sent_ideal, '.-', label = 'ideal', color = 'r')
plt.plot(range(len(total_real)), total_real, '.-', label = 'total real')
#plt.plot(range(len(total_ideal)), total_ideal, '-', label = 'total ideal')
#plt.bar(range(len(sub)), sub, label = 'real - ideal')
print(statistics.mean(sub))
print(statistics.variance(sub))

plt.legend()
plt.xlabel('Frame')
plt.ylabel('Size (kb)')
plt.title('Layer Status')

plt.show()