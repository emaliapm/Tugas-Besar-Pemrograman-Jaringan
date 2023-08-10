import socket
import threading
import os

class Client:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ('192.168.1.85', 8080)  # Replace with the IP address of the server machine
        self.client_socket.connect(self.server_address)
        self.username = input("Username: ")
        self.client_socket.send(bytes(self.username, encoding='utf-8'))

        self.receive_thread = threading.Thread(target=self.receive_message)
        self.send_thread = threading.Thread(target=self.send_message)
        self.receive_thread.start()
        self.send_thread.start()

    def send_message(self):
        while True:
            try:
                print("Select an option:")
                print("1. Send Message (Unicast)")
                print("2. Send Message (Multicast)")
                print("3. Send Message (Broadcast)")
                print("4. Send File")
                print("5. Exit")
                option = input()

                if option == "1":
                    recipient = input("Masukkan nama penerima pesan: ")
                    message = input("Masukkan pesan: ")
                    self.client_socket.send(bytes(f'@{recipient}:{message}', encoding='utf-8'))

                elif option == "2":
                    recipient = 'multicast'
                    daftar_user = list(input("Pilih User (Multi gunakan koma untuk split misal a,b) : ").split(","))
                    message = input("Masukkan pesan multicast: ")
                    for x in daftar_user:
                        self.client_socket.send(bytes(f'@{x}:{message}', encoding='utf-8'))

                elif option == "3":
                    recipient = 'broadcast'
                    message = input("Masukkan pesan broadcast: ")
                    self.client_socket.send(bytes(f'@{recipient}:{message}', encoding='utf-8'))

                elif option == "4":
                    self.send_file()

                elif option == "5":
                    print("Exiting the client.")
                    self.client_socket.close()
                    break

                else:
                    print("Invalid option. Try again.")

            except Exception as e:
                print(f"Terjadi kesalahan saat mengirim pesan atau file: {e}")
                self.client_socket.close()
                break
            
    def receive_message(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message.startswith("file:"):
                    self.receive_file(message[5:])
                else:
                    print(message)
            except Exception as e:
                print(f"Terjadi kesalahan pada koneksi dengan server: {e}")
                self.client_socket.close()
                break

    def receive_file(self, file_info):
        try:
            file_size, file_name, relative_folder, sender_username = file_info.split(':', 3)
            file_size = int(file_size)

            file_path = os.path.join(relative_folder, file_name)
            with open(file_path, 'wb') as file:
                remaining_bytes = file_size
                while remaining_bytes > 0:
                    data = self.client_socket.recv(1024)
                    file.write(data)
                    remaining_bytes -= len(data)

            print(f"File '{file_name}' berhasil diterima.")
        except Exception as e:
            print(f"Terjadi kesalahan saat menerima file: {e}")

    def send_file(self):
        try:
            recipient = input("Masukkan nama penerima file (broadcast/multicast/username): ")
            file_path = input("Masukkan path file yang akan dikirim: ")
            if not os.path.exists(file_path):
                print("File tidak ditemukan.")
                return

            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_size = len(file_data)

            file_info = f"{file_size}:{os.path.basename(file_path)}:.:{recipient}"
            self.client_socket.sendall(bytes(f"file:{file_info}", encoding='utf-8'))
            self.client_socket.sendall(file_data)
            print("File berhasil dikirim.")

        except Exception as e:
            print(f"Terjadi kesalahan saat mengirim file: {e}")


if __name__ == "__main__":
    Client()