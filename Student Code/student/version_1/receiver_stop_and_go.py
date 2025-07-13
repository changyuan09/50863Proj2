from monitor import Monitor
import sys
import time

# Config File
import configparser

if __name__ == '__main__':
    print("Receiver starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    recv_monitor = Monitor(config_path, 'receiver')
    
    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    sender_id = int(cfg.get('sender', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
    max_packet_size -= 12  # Account for the header size
    write_location = cfg.get('receiver', 'write_location')
    print('Receiver: Waiting for file contents...')
    #listen for contents of file and sending ACKs
    #open file to write to
    with open(write_location, 'wb') as f:
        received_list = []
        data_list = []
        received_count = 0
        while True:
            addr, data = recv_monitor.recv(max_packet_size)
            if data == b'':
                break
            
            received_id = int.from_bytes(data[:4], byteorder='big')
            
            data = data[4:]
            if received_count == received_id + 1:
                received_count = received_id
            
            if received_id in received_list:
                if data not in data_list:
                    f.write(data)
                    data_list.append(data)
            elif data in data_list:
                print(f'Receiver: Duplicate data from id {data}.')
            else:
                f.write(data)
                received_list.append(received_id)
                data_list.append(data)
            recv_monitor.send(sender_id, b'ACK' + received_count.to_bytes(4, byteorder='big'))
            
            if received_id == received_count: 
                received_count += 1
    f.close()
    recv_monitor.recv_end(write_location, sender_id)