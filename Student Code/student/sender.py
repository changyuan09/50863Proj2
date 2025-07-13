from monitor import Monitor
import sys
import configparser
import time
import socket
from collections import deque

# Timeout period in seconds
timeout = 0.22

def create_package(chunk_dict, window_size, loop_counter):
    for i in range(window_size):
        chunk_dict[loop_counter + i] = chunk[i * max_packet_size : (i + 1) * max_packet_size]
        
def send_packets(chunk_dict, send_monitor, receiver_id, window_size):
    keys_list = sorted(list(chunk_dict.keys()))  # Convert to a sorted list

    for i in range(window_size):
        header = keys_list[i].to_bytes(4, byteorder='big')
        send_monitor.send(receiver_id, header + chunk_dict[keys_list[i]])
    print(f"first chunk sent is {list(chunk_dict.keys())}")

if __name__ == '__main__':
    print("Sender starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    send_monitor = Monitor(config_path, 'sender')
    send_monitor.socketfd.settimeout(1)

    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    receiver_id = int(cfg.get('receiver', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE')) - 8  # Account for header size
    window_size = int(cfg.get('sender', 'window_size'))

    # Open the file for reading in chunks
    with open(file_to_send, 'rb') as f:
        # send_count = 0
        chunk_copy = b''
        first_packet = True
        chunk_dict = {}
        chunk_dict_copy = {}
        loop_counter = 0
        resend_count = 0
        while True:
            chunk = f.read(max_packet_size * window_size)

            if not chunk:
                # Send an empty packet to signal end of transmission
                send_monitor.send(receiver_id, b'')
                print("last chunk sent!!!")
                break

            if first_packet == True:
                create_package(chunk_dict, window_size, loop_counter)
                # First packet sent directly
                ack_received_firsttime = False
                while not ack_received_firsttime:
                    try:
                        addr, data = send_monitor.recv(max_packet_size)
                    except socket.timeout:
                        # Timeout → Retransmit last packet
                        send_packets(chunk_dict, send_monitor, receiver_id, window_size)
                        data = b''
                        #print(f"retransmission {list(chunk_dict.keys())}")
                     # Check if received ACK matches expected sequence number
                    if data == b'ACK' + (max(chunk_dict.keys())).to_bytes(4, byteorder='big'):
                        # ACK received, send next packet
                        ack_received_firsttime = True
                        chunk_dict_copy = chunk_dict.copy()
                        loop_counter += 1
                        first_packet = False
                        print(f'first time transmitting, received ACK {data}, counter is {loop_counter}')
                        send_monitor.socketfd.settimeout(timeout)
                        break                   
                    else:
                        print(f'first time transmitting waiting for data {data}')

                continue
            elif first_packet == False:
                chunk_dict = {}
                for i in range(window_size):
                    start_index = i * max_packet_size
                    end_index = (i + 1) * max_packet_size
                    chunk_dict[loop_counter * window_size + i] = chunk[start_index:end_index]
                send_packets(chunk_dict, send_monitor, receiver_id, window_size)
                #import pdb; pdb.set_trace()
            else:
                # Wait for ACK before sending next packet
                print("A!!!!!!!!!")
            
            ack_received = False
            while not ack_received:
                try:
                    addr, data = send_monitor.recv(max_packet_size)
                except socket.timeout:
                    # Timeout → Retransmit last packet
                    #####send_packets(chunk_dict, send_monitor, receiver_id, window_size)#######
                    data = b''
                    #print(f"retransmission {list(chunk_dict.keys())}")
                    
                # Check if received ACK matches expected sequence number
                if data == b'ACK' + (max(chunk_dict.keys())).to_bytes(4, byteorder='big'):
                    # ACK received, send next packet
                    #send_three_packets(chunk_dict, send_monitor, receiver_id)
                    ack_received = True
                    chunk_dict_copy = chunk_dict.copy()
                    loop_counter += 1
                    print(f'later transmitting, received ACK {data}, counter is {loop_counter}')
                elif data.startswith(b'NACK'):
                    number = int.from_bytes(data[4:8], byteorder='big')
                    if number in chunk_dict:
                        header = number.to_bytes(4, byteorder='big')  # Convert to 4-byte header
                        send_monitor.send(receiver_id, header + chunk_dict[number])  # Resend packet
                        print(f"Extracted NACK: {data} ; Resending chunk {number}")
                        resend_count += 1
                    elif number > max(chunk_dict.keys()):
                        print(f"Future NACK request{data}. SKIP current iteration")
                        break
                    else:
                        print("DEBUGGG")
                else:
                    print(f'else condition!!!!!!data is {data}')
                            
    print(f'Sender: File {file_to_send} sent to receiver.')
    f.close()
    print(f"Resend {resend_count} packets")
    # Ensure receiver completes before terminating the sender
    time.sleep(1.5)
    send_monitor.send_end(receiver_id)