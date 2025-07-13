from monitor import Monitor
import sys
import configparser
import time
import socket

if __name__ == '__main__':
    print("receiver starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    receiver_monitor = Monitor(config_path, 'receiver')

    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    sender_id = int(cfg.get('sender', 'id'))
    receiver_id = int(cfg.get('receiver', 'id'))
    write_location = cfg.get('receiver', 'write_location')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))  # Account for header size
    window_size = int(cfg.get('sender', 'window_size'))
    print('Receiver: Waiting for file contents...')

    with open(write_location, 'wb') as f:
        previous_data = {}
        received_data = {}
        ACK_count = 0
        first_packet = True

        while True:
            try:
                addr, data = receiver_monitor.recv(max_packet_size)  # Attempt to receive data
                if data == b'':
                    break
                ####################################received_header_classification
                received_header = int.from_bytes(data[:4], byteorder='big')
                print(f"received header {received_header} received data{list(received_data.keys())} previous_data{list(previous_data.keys())}")
                if received_header not in received_data and received_header not in previous_data:
                    received_data[int.from_bytes(data[:4], byteorder='big')] = data[4:]
                elif received_header in previous_data and len(previous_data) == window_size:
                    key = sorted(list(previous_data.keys()))
                    receiver_monitor.send(sender_id, b'ACK' + max(key).to_bytes(4, byteorder='big'))
                    #print(f"send max key again {key}")
                    continue
                ########################################################################
            except socket.timeout:
                continue

            # if (received_header) == 5 and len(received_data) == 3:
            #     import pdb; pdb.set_trace()
            #print(f"received_data is {received_data}")
            if first_packet == True and len(received_data) == window_size:
                key = sorted(list(received_data.keys()))
                to_match_list = [ACK_count + i for i in range(window_size)]
                if key == to_match_list:
                    first_packet = False
                    f.write(b''.join(received_data[k] for k in key))
                    receiver_monitor.send(sender_id, b'ACK' + max(key).to_bytes(4, byteorder='big'))
                    ACK_count += 1
                    previous_data = received_data.copy()
                    received_data = {}
                    # f.close()
                    # break
                    #print(f"received first packet key is {key}")
                    continue
                else:
                    #print(f"firsttime receiving data and key is {key}")
                    pass
            
            if first_packet == False and len(received_data) == window_size:
                key = sorted(list(received_data.keys()))
                to_match_list = [(ACK_count * window_size + i) for i in range(window_size)]
                if key == to_match_list:
                    f.write(b''.join(received_data[k] for k in key))
                    receiver_monitor.send(sender_id, b'ACK' + max(key).to_bytes(4, byteorder='big'))
                    previous_data = received_data.copy()
                    ACK_count += 1
                    received_data = {}
                    #print(f"received later packet key is {key} ACK_count is {ACK_count}")
                else:
                    pass

    receiver_monitor.recv_end(write_location, sender_id)
    f.close()
            # if first_packet == True:
            #     if ack_received != 0:
            #         continue
            #     elif ack_received == 0:
            #         ACK.append(ack_received)
            #         first_packet = False
            #         receiver_monitor.send(sender_id, b'ACK' + ack_received.to_bytes(4, byteorder='big'))
            #         f.write(chunk)
            #         #ACK_count += 1
            #     else:
            #         print(f"Something wrong with received ACK: {ack_received}")
            # elif first_packet == False:
            #     if ack_received == ACK[-1] + 1:
            #         f.write(chunk)
            #         ACK.append(ack_received)
            #         receiver_monitor.send(sender_id, b'ACK' + ack_received.to_bytes(4, byteorder='big'))
            #     elif ack_received != ACK[-1] + 1:
            #         receiver_monitor.send(sender_id, b'ACK' + ACK[-1].to_bytes(4, byteorder='big'))
                



# from monitor import Monitor
# import sys
# import time

# # Config File
# import configparser

# if __name__ == '__main__':
#     print("Receiver starting up!")
#     config_path = sys.argv[1]

#     # Initialize sender monitor
#     recv_monitor = Monitor(config_path, 'receiver')
    
#     # Parse config file
#     cfg = configparser.RawConfigParser(allow_no_value=True)
#     cfg.read(config_path)
#     sender_id = int(cfg.get('sender', 'id'))
#     file_to_send = cfg.get('nodes', 'file_to_send')
#     max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
#     max_packet_size -= 12  # Account for the header size
#     write_location = cfg.get('receiver', 'write_location')
#     print('Receiver: Waiting for file contents...')
#     #listen for contents of file and sending ACKs
#     #open file to write to
#     with open(write_location, 'wb') as f:
#         received_count = 0
#         received_list = []
#         data_list = []
#         while True:
#             addr, data = recv_monitor.recv(max_packet_size)
#             if data == b'':
#                 break
#             #print(f'Receiver: Received {len(data)} bytes from id {addr}.')
#             id = int.from_bytes(data[:4], byteorder='big')
#             #print(f'Receiver: Received id {id}.')
#             data = data[4:]
#             if received_count == id + 1:
#                 #print(f'Receiver: POSSIBLE DESCREPANCY.')
#                 #print(f'Receiver: Received id {id} but expected id {received_count}.')
#                 received_count = id
#             if id in received_list:
#                 #print(f'Receiver: Duplicate tag from id {id}.')
#                 if data not in data_list:
#                     f.write(data)
#                     #received_list.append(id)
#                     data_list.append(data)
#                     #print(f'Receiver: Duplicate data from id {id}.')
#             elif data in data_list:
#                 print(f'Receiver: Duplicate data from id {data}.')
#                 #received_count = id
#             else:
#                 f.write(data)
#                 #print(f'Receiver: Writing data {data}.')
#                 received_list.append(id)
#                 data_list.append(data)
#             recv_monitor.send(sender_id, b'ACK' + received_count.to_bytes(4, byteorder='big'))
#             if id == received_count: 
#                 received_count += 1
#     #print(received_list)
#     #print(len(received_list))
#     f.close()
#     recv_monitor.recv_end(write_location, sender_id)
#     # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.





