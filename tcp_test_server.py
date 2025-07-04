import socket, threading, json, time, argparse
from datetime import datetime

class TradingTCPServer:
    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port
        self.running = False
        self.active_strategies = {}
        self.server_socket = None
        self.request_counter = 0

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"🚀 TCP Server started on {self.host}:{self.port}")

            while self.running:
                client_socket, address = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_socket, address), daemon=True).start()

        except Exception as e:
            print(f"❌ Server error: {e}")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            finally:
                self.server_socket.close()
                print("\n🛑 TCP Server stopped")

    def _handle_client(self, client_socket, address):
        try:
            while self.running:
                length_data = self._recv_exact(client_socket, 4)
                if not length_data:
                    break

                try:
                    message_length = int(length_data.decode('utf-8'))
                except ValueError:
                    break

                message_data = self._recv_exact(client_socket, message_length)
                if not message_data:
                    break

                try:
                    request = json.loads(message_data.decode('utf-8'))
                    self.request_counter += 1
                    response = self._process_request(request)
                    response_json = json.dumps(response)
                    response_message = f"{len(response_json):04d}{response_json}"
                    client_socket.sendall(response_message.encode('utf-8'))
                except Exception as e:
                    error_response = {"status": "error", "message": str(e)}
                    self._send_error_response(client_socket, error_response)
        finally:
            client_socket.close()

    def _recv_exact(self, sock, length):
        data = b''
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def _send_error_response(self, client_socket, error_response):
        try:
            response_json = json.dumps(error_response)
            response_message = f"{len(response_json):04d}{response_json}"
            client_socket.sendall(response_message.encode('utf-8'))
        except:
            pass

    def _process_request(self, request):
        action = request.get('action', '')
        data = request.get('data', {})

        if action == 'apply_strategy':
            return self._handle_apply_strategy(data)
        elif action == 'stop_strategy':
            return self._handle_stop_strategy(data)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_apply_strategy(self, data):
        strategy_id = f"{data.get('table_type', 'unknown')}_{data.get('row_id', 0)}"
        self.active_strategies[strategy_id] = {
            'start_time': datetime.now().isoformat(),
            'complete_data': data
        }
        time.sleep(0.1)
        return {
            "status": "success",
            "message": "Strategy applied successfully",
            "strategy_id": strategy_id,
            "timestamp": datetime.now().isoformat()
        }

    def _handle_stop_strategy(self, data):
        strategy_id = f"{data.get('table_type', 'unknown')}_{data.get('row_id', 0)}"
        self.active_strategies.pop(strategy_id, None)
        time.sleep(0.1)
        return {
            "status": "success",
            "message": "Strategy stopped successfully",
            "strategy_id": strategy_id,
            "timestamp": datetime.now().isoformat()
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', type=int, default=9999)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()

    server = TradingTCPServer(host=args.host, port=args.port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server")
    finally:
        server.stop()

if __name__ == "__main__":
    main()
