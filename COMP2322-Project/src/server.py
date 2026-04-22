import socket
import threading
import os
import time
import datetime
from urllib.parse import unquote


HOST = '127.0.0.1'
PORT = 8080
DOCUMENT_ROOT = './www'
LOG_FILE = 'server.log'

MEDIA_TYPES = {
    '.html': 'text/html',
    '.htm': 'text/html',
    '.txt': 'text/plain',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
}

STATUS_MESSAGES = {
    200: 'OK',
    400: 'Bad Request',
    403: 'Forbidden',
    404: 'File Not Found',
    304: 'Not Modified',

}


def logging(client_ip, access_time, requested_file, response_code):
    with open(LOG_FILE, 'a') as log:
        log.write(f"{client_ip} --- [{access_time}] \"GET {requested_file}\" {response_code}\n")

def find_media_type(file_path):
    extension = os.path.splitext(file_path)[1].lower()
    return MEDIA_TYPES.get(extension, 'application/octet-stream')

def find_file_last_modified(file_path):
    if os.path.exists(file_path):
        modified_time = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(modified_time).strftime('%a, %d %b %Y %H:%M:%S GMT')
    return None


def get_header(request):
    lines = request.split('\r\n')
    if not lines:
        return None, None, None

    request_line = lines[0].split()
    if len(request_line) != 3:
        return None, None, None

    method, path, version = request_line

    headers = {}
    for line in lines[1:]:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value

    return method, path, headers


def handle_client(client_socket, client_address):
    try:
        request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        if not request_data:
            client_socket.close()
            return

        method, raw_path, headers = get_header(request_data)
        if not method or not raw_path:
            send_error_response(client_socket, 400)
            logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'),raw_path if raw_path else 'unknown', 400)
            client_socket.close()
            return
        path = unquote(raw_path)

        if '..' in path or path.startswith('/..'):
            send_error_response(client_socket, 403)
            logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'), raw_path, 403)
            client_socket.close()
            return

        if path == '/' or path == '':
            path = '/index.html'

        file_path = DOCUMENT_ROOT + path

        if not os.path.exists(file_path):
            send_error_response(client_socket, 404)
            logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'), raw_path, 404)
            client_socket.close()
            return

        if not os.path.isfile(file_path):
            send_error_response(client_socket, 403)
            logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'), raw_path, 403)
            client_socket.close()
            return

        if method == 'GET':
            if_modified_since = headers.get('If-Modified-Since')
            last_modified = find_file_last_modified(file_path)

            if if_modified_since and last_modified:
                if if_modified_since == last_modified:
                    send_error_response(client_socket, 304)
                    logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'), raw_path, 304)
                    client_socket.close()
                    return

            send_get_response(client_socket, file_path)
            logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'), raw_path, 200)

        elif method == 'HEAD':
            send_header_response(client_socket, file_path)
            logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'), raw_path, 200)

        else:
            send_error_response(client_socket, 400)
            logging(client_address[0], datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'), raw_path, 400)

        connection_header = headers.get('Connection', '').lower()
        if connection_header == 'close':
            client_socket.close()
        else:
            client_socket.close()

    except Exception as e:
        print(f"Error: {e}")
        try:
            send_error_response(client_socket, 400)
        except:
            pass
        client_socket.close()



def send_header_response(client_socket, file_path):
    try:
        file_size = os.path.getsize(file_path)
        mime_type = find_media_type(file_path)
        last_modified = find_file_last_modified(file_path)

        response = f"HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: {mime_type}\r\n"
        response += f"Content-Length: {file_size}\r\n"
        if last_modified:
            response += f"Last-Modified: {last_modified}\r\n"
        response += f"Connection: keep-alive\r\n"
        response += f"\r\n"

        client_socket.send(response.encode())
    except Exception as e:
        print(f"Error in HEAD: {e}")
        send_error_response(client_socket, 404)


def send_get_response(client_socket, file_path):
    try:
        file_size = os.path.getsize(file_path)
        mime_type = find_media_type(file_path)
        last_modified = find_file_last_modified(file_path)

        response_headers = f"HTTP/1.1 200 OK\r\n"
        response_headers += f"Content-Type: {mime_type}\r\n"
        response_headers += f"Content-Length: {file_size}\r\n"
        if last_modified:
            response_headers += f"Last-Modified: {last_modified}\r\n"
        response_headers += f"Connection: keep-alive\r\n"
        response_headers += f"\r\n"

        client_socket.send(response_headers.encode())

        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                client_socket.send(chunk)

    except Exception as e:
        print(f"Error in GET: {e}")
        send_error_response(client_socket, 404)


def send_error_response(client_socket, status_code):
    message = STATUS_MESSAGES.get(status_code, 'Internal Server Error')
    body = f"<html><body><h1>{status_code} {message}</h1></body></html>"

    response = f"HTTP/1.1 {status_code} {message}\r\n"
    response += f"Content-Type: text/html\r\n"
    response += f"Content-Length: {len(body)}\r\n"
    response += f"Connection: close\r\n"
    response += f"\r\n"
    response += body

    client_socket.send(response.encode())


def run_server():
    if not os.path.exists(DOCUMENT_ROOT):
        os.makedirs(DOCUMENT_ROOT)
        with open(os.path.join(DOCUMENT_ROOT, 'index.html'), 'w') as f:
            f.write("<html><body><h1>Welcome to the Web Server!</h1></body></html>")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"Web server running on http://{HOST}:{PORT}")
    print(f"Document root: {DOCUMENT_ROOT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")

            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()


if __name__ == '__main__':
    run_server()