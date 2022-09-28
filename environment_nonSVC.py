import random
import datetime
import os
import statistics

MILLISECONDS_IN_SECOND = 1000.0
B_IN_MB = 1000000.0
BITS_IN_BYTE = 8.0

# at stage 1: we assume the uploading and downloading processes are both all-i encoding so all frames are
# independent from each other
RTT = 0 # round trip time

# video configurations
FPS = 25.0
frame_time = 1/FPS
video_duration = 20 # seconds
total_frame_number = FPS * video_duration
discount_factor = 0.8

# set the constant frame size (maximum value)
frame_size_max = 2000 #kb (all-i 50 mbps CBR, the best possible images from the sensors)
frame_size_min = 25 #kb (minimum value for a frame that is worth transferring, lower than that would be pointless for poor quality)

# playback settings
initial_buffers = 1 # seconds
target_buffers = 1 # seconds
upstream_buffers = 0.02 # seconds

# Network information
data_segment_size = 1472 # bytes/from Showing Data

# Part one: uploading part

# read the network packet trace data
NETWORK_TRACE = '3HK'
network_trace_dir = './network_trace/' + NETWORK_TRACE + '/'
cooked_files = os.listdir(network_trace_dir)
all_packet_arrival_time = []
all_packet_size = []
all_file_names = []
all_instant_speed = []
network_TP_history = []
# read the data into a list
for cooked_file in cooked_files:
    # temporary lists
    file_path = network_trace_dir + cooked_file
    packet_arrival_time = []
    packet_size = []
    instant_speed = []
    with open(file_path, 'rb') as f:
        serial = 0
        relative_start = 0
        for line in f:
            parse = line.split()
            if serial == 0:
                packet_arrival_time.append(0)
                relative_start = float(parse[0])
            else:
                packet_arrival_time.append(float(parse[0])-relative_start)
                if packet_arrival_time[-1] == packet_arrival_time[-2]:
                    # check if there are duplicates in timecodes
                    print(float(parse[0]))
                    print("there are duplicates")
                else:
                    instant_speed.append(float(parse[1])*8/(packet_arrival_time[-1]-packet_arrival_time[-2])/1000)  # kbps
            serial = serial+1
            packet_size.append(float(parse[1]))

        all_instant_speed.append(instant_speed)
        all_packet_arrival_time.append(packet_arrival_time)
        all_packet_size.append(packet_size)
        all_file_names.append(cooked_file)


for p in range(int(len(all_file_names))):
# check if the network trace data is long enough for current video playback
    if all_packet_arrival_time[p][-1] >= video_duration + initial_buffers:
        # initialization
        frame_send_time = []
        frame_cdn_arrival_time = []
        total_frame_size = []
        estimated_frame_size = []
        sent_frame_size = []
        delay_time = []
        bandwidth_usable = []
        real_time = 0
        frame_loss = 0
        arrive_on_time = 0
        
        # read the size of the layers of the encoded video from video trace data file
        data = []
        with open('./video_trace/idealSVC_352_288_2.txt', 'rb') as f:
            data = f.readlines()
        
        # during initial buffer, send out the original frame
        for i in range(int(total_frame_number)):
            print("Frame", i + 1, "Generated time:", i * frame_time)
            flag = 0

            # todo: put uploading ABR algorithms here, including live streaming, on demand streaming ABR algorithms
            # simple mean estimation algorithm for frame size prediction using the throughput history
            next_frame_size = 10
            if len(network_TP_history) >= 10:
                next_frame_size = statistics.mean(network_TP_history[-5:-1]) * frame_time * discount_factor
            estimated_frame_size.append(next_frame_size)
            
            # calculate the total frame size
            frame_size = 0.0
            for j in range(8):
                frame_size = frame_size + float(data[8*i+j]) / 1000
            total_frame_size.append(frame_size)
            
            # if frame size too large then adjust to the estimate size
            if frame_size > next_frame_size:
                frame_size = next_frame_size
            sent_frame_size.append(frame_size)
            
            
            # check whether at this time the frame is available to send
            if real_time >= i * frame_time:
                frame_send_time.append(real_time)
            else:
                # the frame hasn't been generated yet, wait till it is ready to send it
                real_time = i * frame_time
                frame_send_time.append(real_time)
                
            # calculate CDN arrival time, by using the packet trace
            # instead of using the precise arrival time of each packet, we use linear interpolation to estimate the
            # throughput using the packets every given interval (e.g. 0.1s) so that we could calculate the arrival time of each
            # frame more easily
            for k in range(len(all_packet_arrival_time[p])):
                if all_packet_arrival_time[p][k] <= real_time and all_packet_arrival_time[p][k+1] > real_time:
                    break

            # Sent the frame
            transmission_time = 0.0
            tmp_time = real_time
            while flag == 0:
                if frame_size - all_instant_speed[p][k] * (all_packet_arrival_time[p][k+1] - tmp_time) > 0:
                    frame_size = frame_size - all_instant_speed[p][k] * (all_packet_arrival_time[p][k+1] - tmp_time)
                    transmission_time = transmission_time + all_packet_arrival_time[p][k+1] - tmp_time
                    tmp_time = all_packet_arrival_time[p][k+1]
                    
                    # if exceed the next frame generated time + 0.02s buffer, stop upload immediately
                    if transmission_time + real_time >= (i + 1) * frame_time + upstream_buffers:
                        transmission_time = upstream_buffers + (i + 1) * frame_time - real_time
                        frame_loss = frame_loss + 1
                        flag = 1
                        break

                    k = k + 1
                else:
                    # calculate the exact arrival time of each frame at the CDN server
                    transmission_time = transmission_time + frame_size / all_instant_speed[p][k]
                    tmp_time = tmp_time + frame_size / all_instant_speed[p][k]

                    # if exceed the next frame generated time + 0.02s buffer, stop upload immediately
                    if transmission_time + real_time >= (i + 1) * frame_time + upstream_buffers:
                        transmission_time = upstream_buffers + (i + 1) * frame_time - real_time
                        frame_loss = frame_loss + 1
                        flag = 1
                    break
            
            real_time = real_time + transmission_time
            frame_cdn_arrival_time.append(real_time)
            
            #if frame loss then size = 0
            if flag == 1:
                sent_frame_size[-1] = 0.0
            else:
                # record delay, if frame loss then delay = 0 since no playback at the receiver side
                delay_time.append(real_time - i * frame_time)
                network_TP_history.append(sent_frame_size[-1] / transmission_time)
                
            # record whether the frame arrives on time
            if real_time <= (i + 1) * frame_time and sent_frame_size[-1] != 0.0:
                arrive_on_time = arrive_on_time + 1
  
            # estimate the packet size from the sent time to the next sent time
            for k in range(len(all_packet_arrival_time[p])):
                if all_packet_arrival_time[p][k] <= frame_send_time[-1] and all_packet_arrival_time[p][k+1] > frame_send_time[-1]:
                    break
            
            flag = 0
            estimate_packet_size = 0.0
            tmp_time = frame_send_time[-1]
            if frame_cdn_arrival_time[-1] <= (i + 1) * frame_time:
                next_time = (i + 1) * frame_time
            else:
                next_time = frame_cdn_arrival_time[-1]
            
            while flag == 0:
                if all_packet_arrival_time[p][k+1] <= next_time:
                    estimate_packet_size = estimate_packet_size + all_instant_speed[p][k] * (all_packet_arrival_time[p][k+1] - tmp_time)
                    tmp_time = all_packet_arrival_time[p][k+1]
                else:
                    estimate_packet_size = estimate_packet_size + all_instant_speed[p][k] * (next_time - tmp_time)
                    break
                k = k + 1
            bandwidth_usable.append(estimate_packet_size)

            print("Frame size =", sent_frame_size[-1])
            print(estimate_packet_size, next_frame_size)
            print("Sent time:", frame_send_time[-1], "Arrive time:", frame_cdn_arrival_time[-1])
            print("")


        # print a summary
        print("\n")
        print("-------------------------Summary-------------------------\n")
        print("Non-SVC DF =", discount_factor)
        print("Frame arrive on time:", arrive_on_time, "time(s)  Percentage:", arrive_on_time / total_frame_number * 100)
        print("Average delay time =", statistics.mean(delay_time) * 1000, "ms")
        print("Frame loss rate =", frame_loss,"/",int(total_frame_number),"=",float(frame_loss / total_frame_number))
        print("")
        print("Estimated frame size =", statistics.mean(estimated_frame_size))
        print("Usable bandwidth =", statistics.mean(bandwidth_usable))
        print("Sent frame size =", statistics.mean(sent_frame_size))
        print("")
        print("Bandwidth utilization = %.2f" % (statistics.mean(sent_frame_size) / statistics.mean(bandwidth_usable) * 100))
        print("Uploaded percentage = %.2f" % (statistics.mean(sent_frame_size) / statistics.mean(total_frame_size) * 100))
        
        if frame_loss + len(delay_time) != total_frame_number:
            print("A bug occurs!")


    print("\nReading data to file")
    with open('./result/nonSVC.txt', 'a+') as f:
        tmp1 = statistics.mean(delay_time) * 1000
        tmp2 = statistics.mean(sent_frame_size)
        tmp3 = sum(sent_frame_size) / sum(bandwidth_usable) * 100
        tmp4 = frame_loss
        f.write('%f %f %f %d' % (tmp1, tmp2, tmp3, tmp4))
        f.write('\n')
    f.close()

print("End of program")