import socket
import time

import argparse


class URUtil:

    def __init__(self, host = "192.168.1.59", port=30002):
        self.HOST = host
        self.PORT = port

    def runScriptWithContent(self, content):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)

        s.connect((self.HOST, self.PORT))
        
         # Read the content in blocks of 1024 bytes and send each block
        block_size = 1024
        for i in range(0, len(content), block_size):
            block = content[i:i + block_size]
            s.sendall(block.encode('utf-8'))  # Encode the block to bytes and send it
            # s.sendall(block)
            print(f"Sent block {i // block_size + 1}")

        s.close()

        print("Closed")
        
    def runScript(self, scriptFile):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)

        s.connect((self.HOST, self.PORT))
        f = open(scriptFile, "rb")

        l = f.read(1024)
        while(l):
            s.send(l)
            l = f.read(1024)
        s.close()

        print("Closed")


if __name__ == '__main__':
    # urutil = URUtil("192.168.2.52")
    parser = argparse.ArgumentParser(description='Enter server ip')
    parser.add_argument('--host', nargs='?', help='server ip',  default='192.168.2.52')
    parser.add_argument('--script', nargs='?', help='script file',  default='conn_vrc/PRG004.script')
    
    args = parser.parse_args()
    
    urutil = URUtil(args.host)
    urutil.runScript(args.script)