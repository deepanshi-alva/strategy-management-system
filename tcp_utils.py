import socket
import threading
import json

def send_tcp_command(command_dict, callback=None, host='127.0.0.1', port=9999):
    def client_thread():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))
                
                # Encode message with 4-digit length prefix
                message = json.dumps(command_dict)
                length_prefix = f"{len(message):04d}"
                full_message = length_prefix + message
                sock.sendall(full_message.encode('utf-8'))

                # Receive 4-byte length prefix
                response_length_data = sock.recv(4)
                if not response_length_data:
                    raise ValueError("No response length received")
                response_length = int(response_length_data.decode('utf-8'))

                # Receive the actual response body
                response_data = b""
                while len(response_data) < response_length:
                    chunk = sock.recv(response_length - len(response_data))
                    if not chunk:
                        break
                    response_data += chunk

                response = json.loads(response_data.decode('utf-8'))

                if callback:
                    callback(response)

        except Exception as e:
            print("TCP Error:", e)
            if callback:
                callback({"status": "error", "error": str(e)})

    threading.Thread(target=client_thread, daemon=True).start()
