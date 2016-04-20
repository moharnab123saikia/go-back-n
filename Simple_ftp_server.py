import socket
import time
import os
import random
import sys
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

def send_ack(seq_num, server_sockfd, address, ZERO_FIELD, ACK_FIELD):
    send_seq_num = '{0:032b}'.format(seq_num)
    msg_to_be_sent = send_seq_num + ZERO_FIELD + ACK_FIELD
    server_sockfd.sendto(msg_to_be_sent, address)

def check_parameters():
    if len(sys.argv) != 4:
        print "Usage: Simple_ftp_server port# file-name p "
        sys.exit(0)

def checksum(msg):
    total = 0
    for i in range(0, len(msg), 16):
        int_num = int(msg[i:i + 16], 2)
        total = total + int_num;
        if (total >= 65535):
            total -= 65535
    if(total == 0):
        return 1
    else:
        return 0


def parse_data(message):
    write_data = ""
#     print type(str(text_from_bits(message)))
    write_data += str(text_from_bits(message))
    return write_data
#     iterations = len(message) / 8 # print "Received message is %s" % message
#     for i in range(0, iterations):
#         bit_data = str(message[i * 8:(i + 1) * 8])
#         char_data = chr(int(bit_data, 2))
#         write_data += char_data
#     return write_data

def write_data(message, output_file):
    write_data = parse_data(message)
    with open(output_file, 'ab') as myfile:
        myfile.write(write_data)

def parse_cmd():
    server_port = sys.argv[1]
    file_name = sys.argv[2]
    prob = sys.argv[3]
    return int(server_port), file_name, float(prob)

if __name__ == "__main__":
    global seq_num, ZERO_FIELD, ACK_FIELD
    ZERO_FIELD = '0000000000000000'
    ACK_FIELD = '1010101010101010'
#     check_parameters()
#     server_port, file_name, prob = parse_cmd()
    
    server_hostname = socket.gethostname()
    timestr = time.strftime("%Y%m%d-%H%M%S")
    

    server_port = 7735
    file_name = 'file_' + str(timestr) + '.txt'
    prob = 0.01
    prob_int = int(prob * 100)
    
    
    # print server_hostname
    # print server_port
    # print file_name
    # print probability
    
    if(os.path.isfile(file_name)):
        os.remove(file_name)
    
    
    server_sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    server_sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)                        
    server_sockfd.bind((server_hostname, server_port))        
    
    data, address = server_sockfd.recvfrom(32768)
    # print data
    
    
    seq_num = 0
    
    while True:
        data, address = server_sockfd.recvfrom(32768)
        if(data == "File_sent"):
            break
        recv_seq_num = int(data[0:32], 2)
        if(recv_seq_num == seq_num):
            random_p = random.random()
            if(random_p >= prob):
                #recv_seq_num = int(data[0:32], 2)
                if(checksum(data)):
                    if(recv_seq_num == seq_num):
                        seq_num += 1
                        new_data = data[64:]
                        write_data(new_data, file_name)
                        send_ack(seq_num, server_sockfd, address, ZERO_FIELD, ACK_FIELD)          
                else:
                    print "Checksum failed, sequence number = %d" % recv_seq_num
            else:
                print "Packet loss, sequence number = %d" % recv_seq_num
        else:
            if(recv_seq_num < seq_num):
                print "Received duplicate packet with sequence number = %d" % recv_seq_num
            else:
                recv_seq_num = int(data[0:32], 2)
                
    print "File received successfully"
    
    
    
    
    




