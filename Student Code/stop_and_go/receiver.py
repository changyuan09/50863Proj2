from monitor import Monitor
import sys
import configparser
import time
import socket

timeout = 0.22
def NACK_send(received_data, ACK_count, send_monitor, sender_id, window_size):
    key = sorted(list(received_data.keys()))
    expected_start = (ACK_count * window_size)
    expected_end = ((ACK_count + 1) * window_size)
    expected_list = list(range(expected_start, expected_end))
    print(f"\nexpected list {expected_list}, key is {key}, ACK_count is {ACK_count}\n")
    missing_elements = sorted(set(expected_list) - set(key))
    for element in missing_elements:
        if len(missing_elements) >= 10:
            receiver_monitor.send(sender_id, b'NACK' + element.to_bytes(4, byteorder='big'))
            time.sleep(0.5)
            break
        receiver_monitor.send(sender_id, b'NACK' + element.to_bytes(4, byteorder='big'))
        print(f"NACK sent {b'NACK' + element.to_bytes(4, byteorder='big')}")

if __name__ == '__main__':
    print("receiver starting up!")
    config_path = sys.argv[1]

    
    receiver_monitor = Monitor(config_path, 'receiver')

   
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    receiver_monitor.socketfd.settimeout(1.5)
    sender_id = int(cfg.get('sender', 'id'))
    receiver_id = int(cfg.get('receiver', 'id'))
    write_location = cfg.get('receiver', 'write_location')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))  
    window_size = int(cfg.get('sender', 'window_size'))
    print('Receiver: Waiting for file contents...')

    with open(write_location, 'wb') as f:
        previous_data = {}
        received_data = {}
        ACK_count = 0
        first_packet = True

        while True:
            try:
                addr, data = receiver_monitor.recv(max_packet_size) 
                if data == b'':
                    print("end of file received")
                    break
                
                received_header = int.from_bytes(data[:4], byteorder='big')

                if received_data != {} and previous_data != {}:
                    print(f"received header {received_header} received data from {min(list(received_data.keys()))} to {max(list(received_data.keys()))} with {len(list(received_data.keys()))} previous_data from {min(list(previous_data.keys()))} to {max(list(previous_data.keys()))} with {len(list(previous_data.keys()))}\n")
                else:
                    print("havent got anything yet")

                if received_header not in received_data and received_header not in previous_data:
                    received_data[int.from_bytes(data[:4], byteorder='big')] = data[4:]
                    keys = sorted(received_data.keys())
                elif received_header in previous_data and len(previous_data) == window_size:
                    key = sorted(list(previous_data.keys()))
                    receiver_monitor.send(sender_id, b'ACK' + max(key).to_bytes(4, byteorder='big'))
                    continue
                
            except socket.timeout:
                
                NACK_send(received_data, ACK_count, receiver_monitor, sender_id, window_size)


            if first_packet == True and len(received_data) == window_size:
                key = sorted(list(received_data.keys()))
                to_match_list = [ACK_count + i for i in range(window_size)]
                if key == to_match_list:
                    first_packet = False
                    f.write(b''.join(received_data[k] for k in key))
                    receiver_monitor.send(sender_id, b'ACK' + max(key).to_bytes(4, byteorder='big'))
                    print(f"ACK sent MAX KEY {max(key)}")
                    ACK_count += 1
                    previous_data = received_data.copy()
                    received_data = {}
                    receiver_monitor.socketfd.settimeout(timeout)
                    continue
                else:
                    pass
            
            if first_packet == False and len(received_data) == window_size:
                key = sorted(list(received_data.keys()))
                to_match_list = [(ACK_count * window_size + i) for i in range(window_size)]
                if key == to_match_list:
                    f.write(b''.join(received_data[k] for k in key))
                    receiver_monitor.send(sender_id, b'ACK' + max(key).to_bytes(4, byteorder='big'))
                    print(f"ACK sent MAX KEY {max(key)}")
                    previous_data = received_data.copy()
                    ACK_count += 1
                    received_data = {}
                else:
                    pass

    receiver_monitor.recv_end(write_location, sender_id)
    f.close()





