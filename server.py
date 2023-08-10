import socket
import threading
from datetime import datetime
import os
import sys

class Server:
    def __init__(self):
        #menyimpan informasi pengguna yg terhubung
        self.user = {}
        self.users_last_message = {}

        #membuat socket server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ('0.0.0.0', 8080) 
        self.server_socket.bind(self.server_address)
        self.server_socket.setblocking(1)
        self.server_socket.listen(3)
        print('Program berjalan pada {} port {}'.format(*self.server_address))
        self.koneksi_baru()

    def koneksi_baru(self):
        while True:
            connection, _ = self.server_socket.accept()
            threading.Thread(target=self.new_client, args=(connection,)).start()

    def new_client(self, connection):
        try:
            client_name = connection.recv(1024).decode('utf-8')
            self.user[connection] = client_name
            self.users_last_message[connection] = False
            print(f'{self.current_time()} {client_name} bergabung!')

            while True:
                data = connection.recv(1024).decode('utf-8')
                if data != '':
                    if data.startswith('@'):
                        recipient, message = data[1:].split(':', 1)
                        self.handle_message(connection, recipient, message)
                        print(f'{self.current_time()} {client_name}:{message}')
                    elif data.startswith('file:'):
                        self.forward_file(connection, data)
                    else:
                        self.broadcast(data, owner=connection)
                else:
                    return
        except Exception as e:
            self.client_disconnection(connection, self.user[connection], str(e))

    def client_disconnection(self, connection, client_name, error_message):
        if connection in self.user:
            print(f'{self.current_time()} {client_name} disconnected.')
            del self.user[connection]
            self.users_last_message.pop(connection)
            connection.close()
        else:
            print(f'{self.current_time()} {client_name} meninggalkan percakapan!')

    def handle_message(self, sender, recipient, message):
        if recipient.lower() == 'broadcast':
            self.broadcast(message, owner=sender)
        elif recipient.lower() == 'multicast':
            self.multicast(message, owner=sender)
        else:
            self.unicast(message, owner=sender, recipient=recipient)

    def send_private_message(self, sender, recipient, message):
        for conn, username in self.user.items():
            if username == recipient:
                data = f'{self.current_time()} {self.user[sender]} (private): {message}'
                conn.sendall(bytes(data, encoding='utf-8'))
                return

    def broadcast(self, message, owner=None):
        for conn in self.user:
            if conn != owner:
                data = f'{self.current_time()} {self.user[owner]} (broadcast): {message}'
                conn.sendall(bytes(data, encoding='utf-8'))

    def multicast(self, message, owner):
        for conn in self.user:
            if conn != owner and self.user[conn] != self.user[owner]:
                data = f'{self.current_time()} {self.user[owner]} (multicast): {message}'
                conn.sendall(bytes(data, encoding='utf-8'))

    def unicast(self, message, owner, recipient):
        for conn in self.user:
            if self.user[conn] == recipient:
                data = f'{self.current_time()} {self.user[owner]} (unicast to {recipient}): {message}'
                conn.sendall(bytes(data, encoding='utf-8'))
                
    def forward_file(self, sender_connection, data):
        try:
            file_info, file_name, relative_folder, recipient_username = data.split(':', 4)[1:]
            file_size = int(file_info)

            if recipient_username.lower() == 'broadcast':
                conns = list(self.user.keys())
            elif recipient_username.lower() == 'multicast':
                conns = [conn for conn in self.user if conn != sender_connection]
            else:
                conns = [conn for conn, username in self.user.items() if username == recipient_username]

            file_info = f"{file_size}:{file_name}:{relative_folder}"
            for recipient_conn in conns:
                recipient_conn.sendall(bytes(f'file:{file_info}:{recipient_username}', encoding='utf-8'))

            received_bytes = 0
            while received_bytes < file_size:
                file_data = sender_connection.recv(4096)
                if not file_data:
                    break

                for recipient_conn in conns:
                    recipient_conn.sendall(file_data)

                received_bytes += len(file_data)

            print(f"\nFile {file_name} berhasil diteruskan ke {recipient_username}")
        except Exception as e:
            print(f"{self.current_time()} Error saat meneruskan file: {str(e)}")
        finally:
            return

    def current_time(self):
        return datetime.now().strftime("%H:%M:%S")

if __name__ == "__main__":
    server = Server()