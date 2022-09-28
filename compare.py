# this code is to compare the difference of dynamic DF results, ideal results and nonSVC results
import os
import statistics
import matplotlib.pyplot as plt

delay = []
upload = []
bandwidth = []
loss = []
with open('./result/nonSVC.txt', 'rb') as f:
    for line in f:
        parse = line.split()
        delay.append(float(parse[0]))
        upload.append(float(parse[1]))
        bandwidth.append(float(parse[2]))
        loss.append(float(parse[3]))
f.close()

delay0 = []
upload0 = []
bandwidth0 = []
loss0 = []
with open('./result/dynamic.txt', 'rb') as f:
    for line in f:
        parse = line.split()
        delay0.append(float(parse[0]))
        upload0.append(float(parse[1]))
        bandwidth0.append(float(parse[2]))
        loss0.append(float(parse[3]))
f.close()

plt.plot(range(len(loss0)), loss0, '.-', label = 'SVC')
plt.plot(range(len(loss)), loss, '.-', label = 'nonSVC')

plt.legend()
plt.xlabel('Network trace data file')
plt.ylabel('Frame loss')
plt.show()


print(statistics.mean(delay))
print(statistics.mean(upload))
print(statistics.mean(bandwidth))
print(statistics.mean(loss))

print(statistics.mean(delay0))
print(statistics.mean(upload0))
print(statistics.mean(bandwidth0))
print(statistics.mean(loss0))