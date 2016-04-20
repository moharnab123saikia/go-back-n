import os
import sys
import socket
import threading
import time
import binascii


def text_to_bits(text, encoding='utf-8', errors='surrogatepass'):
    bits = bin(int(binascii.hexlify(text.encode(encoding, errors)), 16))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def text_from_bits(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return int2bytes(n).decode(encoding, errors)

def int2bytes(i):
    hex_string = '%x' % i
    n = len(hex_string)
    return binascii.unhexlify(hex_string.zfill(n + (n & 1)))


def calculate_checksum(message):
    total = 0
    for i in range(0, len(message), 16):
        data = message[i:i + 16]
        int_num = int(data, 2)
        total += int_num;
        if (total >= 65535):
            total -= 65535
    total = 65535 - total
    checksum_bits = '{0:016b}'.format(total)
    return checksum_bits

def generate_msg(sequence, msg):
    msg_data = ""
    msg_data = text_to_bits(msg)
    sequence_bits = '{0:032b}'.format(sequence)
    message = sequence_bits + "0"*16 + "01"*8 + msg_data
    msg_checksum = calculate_checksum(message)
    final_msg = message[0:32] + msg_checksum + message[48:]
    return final_msg

def receive_ack():
    global seq_num
    global prog_timer
    global index
    while True:
        (data, server) = server_sockfd.recvfrom(8240)
        lock.acquire()
        if(data[48:64] == ACK_STR):
            pass
        else:
            print "Discarding packet: not ACK"
        recv_seq_num = int(data[0:32], 2)
        if(recv_seq_num == (total_packets + 1)):
            seq_num = recv_seq_num
            server_sockfd.sendto("File_sent!", server)
            print "File sent!"
            lock.release()
            break
        if(recv_seq_num > seq_num):
            diff = recv_seq_num - seq_num
            index = index - diff
            seq_num = recv_seq_num
            prog_timer.cancel()
            prog_timer = threading.Timer(timerange, handle_timeout)
            prog_timer.start()
            lock.release()
        else:
            print "Duplicate ack received. No action"
            lock.release()

    
def handle_timeout():
    global total_packets
    global timeout
    if(seq_num <= total_packets):
        print "Timeout, sequence number is %d" % seq_num
    timeout = 1

def file_initial_process(file_name):
    if not os.path.isfile(file_name):
        print "File not present in the given path"
        sys.exit(0)
    
    input_file = open(file_name, "r")
    total_file = input_file.read()
    input_file.close()
    total_packets = len(total_file) / mss
    return total_packets


if __name__ == "__main__":
    
    global ACK_STR
    global lock
    global timerlock
    global seq_num
    global curr_seq_num
    global recv_seq_num
    global window
    global mss
    global total_packets
    global prog_timer
    global timeout
    global timerange
    global index
    
    ACK_STR = "1010101010101010"
    lock = threading.Lock()
    timerlock = threading.Lock()
    seq_num = 0
    timeout = 0
    timerange = 0.5
    index = 0
    
    # server_hostname = str(sys.argv[1])
    # server_port = int(sys.argv[2])
    # file_name = str(sys.argv[3])
    # window = int(sys.argv[4])
    # mss = int(sys.argv[5])
    
    server_hostname = socket.gethostname()
    server_port = 7735
    file_name = "test_file.txt"
    window = 64
    mss = 500
    
    
    start_time = time.time()
    print "Start time: " + str(start_time)
    
    server_sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sockfd.sendto("This is first message", (server_hostname, server_port))

    t1 = threading.Thread(target=receive_ack, args=())
    t1.start()
    
    total_packets = file_initial_process(file_name)
    
    curr_seq_num = seq_num;
    
    prog_timer = threading.Timer(timerange, handle_timeout)
    prog_timer.start()
    while(t1.isAlive()):
        while(index < window):
            input_file = open(file_name, "r")
            lock.acquire()
            if(curr_seq_num != seq_num):
                curr_seq_num = seq_num
            
            temp_index = index
            lock.release();
            input_file.seek((curr_seq_num + temp_index) * mss, 0)
            msg = input_file.read(mss)
            input_file.close()
            if(len(msg) != 0):
                msg_final = generate_msg((temp_index + curr_seq_num), msg)
                index = index + 1
                server_sockfd.sendto(msg_final, (server_hostname, server_port))
            else:
                break
                    
        if(timeout == 1):
            index = 0
            prog_timer = threading.Timer(timerange, handle_timeout)
            prog_timer.start()
            timeout = 0
    
    server_sockfd.close()
    stop_time = time.time()
    
    print "Stop time: " + str(stop_time)
    print "Running Time:" + str(stop_time - start_time)
