from monitor import Monitor
import sys

# Config File
import configparser
import time
import socket
timeout = 0.5  # Timeout period in seconds

if __name__ == '__main__':
    print("Sender starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    send_monitor = Monitor(config_path, 'sender')
    send_monitor.socketfd.settimeout(timeout)
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    file_to_send = cfg.get('nodes', 'file_to_send')
    receiver_id = int(cfg.get('receiver', 'id'))
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
    max_packet_size -= 12 
    # Exchange Messages
    with open(file_to_send, 'rb') as f:
        chunk_copy = b''
        send_count = 0
        first_packet = True
        while True:
            chunk = f.read(max_packet_size)
            if not chunk:
                header = send_count.to_bytes(4, byteorder='big')
                send_monitor.send(receiver_id, b'')
                break
            if first_packet:
                header = send_count.to_bytes(4, byteorder='big')
                send_monitor.send(receiver_id, header + chunk)
                send_count += 1
                chunk_copy = chunk
                first_packet = False
            else:
                ack_received = False
                while not ack_received:
                    try:
                        addr, data = send_monitor.recv(max_packet_size)
                    except socket.timeout:
                        header = (send_count - 1).to_bytes(4, byteorder='big')
                        send_monitor.send(receiver_id, header + chunk_copy)
                        data = b''
                    if data == b'ACK' + (send_count-1).to_bytes(4, byteorder='big'):
                        header = send_count.to_bytes(4, byteorder='big')
                        send_monitor.send(receiver_id, header + chunk)
                        ack_received = True
                        send_count += 1
                        chunk_copy = chunk
                    else:
                        print(f'Sender: Got unexpected data from id: {int.from_bytes(data[3:7], byteorder="big")}. expected: {send_count-1}...')
                        chunk_copy = chunk
    print(f'Sender: File {file_to_send} sent to receiver.')
    f.close()
    time.sleep(1.5)
    send_monitor.send_end(receiver_id)