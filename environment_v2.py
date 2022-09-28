import random
import datetime
import os
import statistics

MILLISECONDS_IN_SECOND = 1000.0
B_IN_MB = 1000000.0
BITS_IN_BYTE = 8.0

# at stage 1: we assume the uploading and downloading processes are both all-i encoding so all frames are
# independent from each other
# value of ideal condition will impact on whether uploading part is ideal or not
ideal_condition = False
RTT = 0 # round trip time

# video configurations
FPS = 25.0
frame_time = 1/FPS
video_duration = 20 # seconds
number_of_layers = 8
total_frame_number = FPS * video_duration
discount_factor = 1

# set the constant frame size (maximum value)
frame_size_max = 2000  #kb (all-i 50 mbps CBR, the best possible images from the sensors)
frame_size_min = 25    #kb (minimum value for a frame that is worth transferring, lower than that would be pointless for poor quality)

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
                    print("There are duplicates")
                    print(float(parse[0]))
                else:
                    instant_speed.append(float(parse[1]) * 8 / 1000 / (packet_arrival_time[-1] - packet_arrival_time[-2]))    # kbps
            serial = serial + 1
            packet_size.append(float(parse[1]))

        all_instant_speed.append(instant_speed)
        all_packet_arrival_time.append(packet_arrival_time)
        all_packet_size.append(packet_size)
        all_file_names.append(cooked_file)


# check if the network trace data is long enough for current video playback
if all_packet_arrival_time[0][-1] >= video_duration + initial_buffers:

    # check whether the test will be run in ideal condition or not
    if ideal_condition == False:

        # A(realistic): upload the optimal frame size based on the network trace data
        # since the trace data can't be known in advance, the uploading time for each frame may exceed 1/fps time
        data = []    # read the data from the video trace data file
        frame_send_time = []
        frame_cdn_arrival_time = []
        estimated_frame_size = []
        all_frame_size = []
        discarded_layer_size = []
        discarded_layer_number = []
        delay_time = []
        bandwidth_usable = []
        arrive_on_time = 0
        frame_loss = 0
        real_time = 0.0

        # read the size of the layers of the encoded video from video trace data file
        with open('./video_trace/idealSVC_352_288_2.txt', 'rb') as f:
            data = f.readlines()

        # upload process for all the frames
        for i in range(int(total_frame_number)):
            print("Frame", i + 1, "Generated time:", i * frame_time)

            # calculate the next frame size which includes all of the layers, in kb
            total_frame_size = 0.0
            for j in range(int(number_of_layers)): 
                total_frame_size = total_frame_size + float(data[number_of_layers * i+j]) / 1000
            all_frame_size.append(total_frame_size)
            
            # check whether at this time the frame is available to send
            if real_time >= i * frame_time:
                frame_send_time.append(real_time)
            else:
                # the frame hasn't been generated yet, wait till it is ready to send it
                real_time = i * frame_time
                frame_send_time.append(real_time)
            
            # bandwidth estimation
            next_frame_size = 10000000
            if len(network_TP_history) >= 10:
                next_frame_size = statistics.mean(network_TP_history[-5:-1]) * frame_time * discount_factor
            print(next_frame_size)

            # calculate the packet size that can be sent, by using the packet trace
            # instead of using the precise arrival time of each packet, we use linear interpolation to estimate the throughput
            # using the packets every given interval (e.g. 0.1s) so that we could calculate the arrival time of each frame more easily
            uploaded_frame_size = 0.0
            transmission_time = 0.0
            
            for k in range(len(all_packet_arrival_time[0])):
                if all_packet_arrival_time[0][k] <= real_time and all_packet_arrival_time[0][k+1] > real_time:
                    break

            # calculate how many layers can be sent (the trace data is unknown in advance)
            flag = 0
            tmp_time = real_time
            for j in range(int(number_of_layers)):
                tmp_size = float(data[number_of_layers * i+j]) / 1000    #layer size, in kb
                # bandwidth estimation
                if uploaded_frame_size + tmp_size >= next_frame_size:
                    break
                while flag == 0:
                    if tmp_size - all_instant_speed[0][k] * (all_packet_arrival_time[0][k+1] - tmp_time) > 0:
                        tmp_size = tmp_size - all_instant_speed[0][k] * (all_packet_arrival_time[0][k+1] - tmp_time)
                        transmission_time = transmission_time + all_packet_arrival_time[0][k+1] - tmp_time
                        tmp_time = all_packet_arrival_time[0][k+1]
                        
                        # if exceed the next frame generated time + 0.02s buffer, stop upload immediately
                        if transmission_time + real_time >= (i + 1) * frame_time + upstream_buffers:
                            transmission_time = upstream_buffers + (i + 1) * frame_time - real_time
                            flag = 1
                            break

                        k = k + 1
                    else:
                        # calculate the exact arrival time of each frame at the CDN server
                        transmission_time = transmission_time + tmp_size / all_instant_speed[0][k]
                        tmp_time = tmp_time + tmp_size / all_instant_speed[0][k]
                        
                        # if exceed the next frame generated time, complete the upload of the current layer
                        if transmission_time + real_time >= (i + 1) * frame_time:
                            flag = 2

                        # if exceed the next frame generated time + 0.02s buffer, stop upload immediately
                        if transmission_time + real_time >= (i + 1) * frame_time + upstream_buffers:
                            transmission_time = upstream_buffers + (i + 1) * frame_time - real_time
                            flag = 1
                        
                        break
                # if hard deadline is reached
                if flag == 1:
                    break
                # layer uploaded
                uploaded_frame_size = uploaded_frame_size + float(data[number_of_layers * i+j]) / 1000
                # if all layers are sent or exceed next frame generated time
                if j == number_of_layers - 1 or flag == 2:
                    j = j + 1
                    break
            
            
            # record the frame size
            estimated_frame_size.append(uploaded_frame_size)
            discarded_layer_size.append(total_frame_size - uploaded_frame_size)
            discarded_layer_number.append(number_of_layers - j)

            # record the network TP and the frame arrival time
            real_time = real_time + transmission_time
            network_TP_history.append(estimated_frame_size[-1] / transmission_time)
            frame_cdn_arrival_time.append(real_time)

            # print the result of uploading the current frame
            if j == number_of_layers:
                print("All layers are sent!")
            else:
                print("Starting from the", j + 1, "layer, the following layer(s) are discarded, size =", total_frame_size - estimated_frame_size[-1], "kb")
            print("Send time:", frame_send_time[-1], "Arrive time:", real_time)
            
            # record frame loss and delay time
            if uploaded_frame_size == 0.0:
                frame_loss = frame_loss + 1
            else:
                delay_time.append(real_time - i * frame_time)

            # record whether the frame arrives on time
            if real_time <= (i + 1) * frame_time and uploaded_frame_size != 0.0:
                arrive_on_time = arrive_on_time + 1

            # estimate the packet size from the sent time to the next sent time
            for k in range(len(all_packet_arrival_time[0])):
                if all_packet_arrival_time[0][k] <= frame_send_time[-1] and all_packet_arrival_time[0][k+1] > frame_send_time[-1]:
                    break
            
            flag = 0
            estimated_packet_size = 0.0
            tmp_time = frame_send_time[-1]
            if frame_cdn_arrival_time[-1] <= (i + 1) * frame_time:
                next_time = (i + 1) * frame_time
            else:
                next_time = frame_cdn_arrival_time[-1]
            
            while flag == 0:
                if all_packet_arrival_time[0][k+1] <= next_time:
                    estimated_packet_size = estimated_packet_size + all_instant_speed[0][k] * (all_packet_arrival_time[0][k+1] - tmp_time)
                    tmp_time = all_packet_arrival_time[0][k+1]
                else:
                    estimated_packet_size = estimated_packet_size + all_instant_speed[0][k] * (next_time - tmp_time)
                    break
                k = k + 1
            
            bandwidth_usable.append(estimated_packet_size)
            print("")

        # print a summary when the upload is completed
        print("\n")
        print("-------------------------Summary-------------------------\n")
        print("Condition: Fix DF = %.2f" % discount_factor)
        print("Frame arrive on time:", arrive_on_time, "time(s)  Percentage:", arrive_on_time / total_frame_number * 100)
        print("Average delay time:", statistics.mean(delay_time) * 1000, "ms")
        print("Frame loss rate =", frame_loss,"/",int(total_frame_number),"=",float(frame_loss / total_frame_number))
        print("")
        print("Uploaded frame size:", statistics.mean(estimated_frame_size), "kb")
        print("Total frame size:", statistics.mean(all_frame_size), "kb")
        print("Discarded layer size:", statistics.mean(discarded_layer_size), "kb")
        print("")
        print("Uploaded percentage: %.2f" % (statistics.mean(estimated_frame_size) / statistics.mean(all_frame_size) * 100))
        print("Discarded percentage: %.2f" % (statistics.mean(discarded_layer_size) / statistics.mean(all_frame_size) * 100))
        print("Number of layer discarded: %.2f" % statistics.mean(discarded_layer_number))
        print("Bandwidth utilization: %.2f" % (sum(estimated_frame_size) / sum(bandwidth_usable) * 100))
        print("")
        print("Instant speed:", statistics.mean(all_instant_speed[0]), "kbps")
        print("Network TP history:", statistics.mean(network_TP_history))


print("\nReading data to file")
with open('../result/layer_SVC_2.txt', 'w+') as f:
    for num in range(int(total_frame_number)):
        tmp1 = float(all_frame_size[num])
        tmp2 = float(estimated_frame_size[num])
        tmp3 = float(discarded_layer_size[num])
        f.write('%f %f %f' % (tmp1, tmp2, tmp3))
        f.write('\n')
f.close()

with open('../result/network_SVC_2.txt', 'w+') as f:
    for num in range(int(len(delay_time))):
        f.write('%f' % delay_time[num])
        f.write('\n')
f.close()

print("End of program")