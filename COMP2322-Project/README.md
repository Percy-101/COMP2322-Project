# COMP2322-Project
Requirements:
- Python 3.6 or higher
- No external libraries required
- Operating System: Windows / Mac / Linux

## To run the server
-Step 1: Open Terminal

-Step 2: Navigate to project folder\
&emsp; &emsp; &emsp; cd ..\COMP2322-Project\src

-Step 3: Run the server:\
&emsp; &emsp; &emsp; python server.py

-Step 4: When server connected:\
&emsp; &emsp; &emsp; Web server running on http://127.0.0.1:8080\
&emsp; &emsp; &emsp; Document root: ./www\
&emsp; &emsp; &emsp; Press Ctrl+C to stop

## To test the server
### Open web browser and enter url below:

    1. Home Page:
       http://127.0.0.1:8080/
    
    2. Text File:
       http://127.0.0.1:8080/test.txt
    
    3. Image File:
       http://127.0.0.1:8080/photo.png
    
    4. 404 Not Found:
       http://127.0.0.1:8080/missing.html

### Using Python console
 1. HEAD Command:\
       import socket\
       s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\
       s.connect(('127.0.0.1', 8080))\
       s.send(b'HEAD /test.txt HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n')\
       print(s.recv(1024).decode())\
       s.close()

 2. 403 Forbidden :
    import socket\
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\
    s.connect(('127.0.0.1', 8080))\
    s.send(b'GET /../../test.txt HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n')\
    print(s.recv(1024).decode())\
    s.close()

 3. 400 Bad Request:
    import socket\
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\
    s.connect(('127.0.0.1', 8080))\
    s.send(b'GET /\r\n\r\n')\
    print(s.recv(1024).decode())\
    s.close()

### TroubleShooting
Problem: "404 Not Found" for existing files
Solution: Make sure files are in ./www folder

Problem: Connection refused
Solution: Make sure server is running before testing