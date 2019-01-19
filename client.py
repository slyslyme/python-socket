import socket
import struct
import os,sys
import operator
import time
import json

buffer=1024

try:
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.connect(('127.0.0.1', 7777))
except socket.error as msg:
    print(msg)
    sys.exit(1)
menu = sk.recv(buffer).decode('utf-8')
print(menu)
print('Please input 【U：Upload】【D：Download】【cmd】【exit】\n')

def socket_client():
    while True:
        print('---------------------------------------')
        data = input('--->').strip()
        data = data.upper()
        if data == 'EXIT':
            sk.send((data.encode('utf-8')))
            break
        elif not data:
            print('Can not empty!')
            continue
        elif data == 'U' or data == 'D':
            sk.send((data.encode('utf-8')))  # 输入上传还是下载
            # 选择上传
            if data == 'U':
                # 输入上传文件的绝对路径
                filepath = input('Please enter the file path to upload\n')
                filename = input('Please input the filename\n')
                path = os.path.join(filepath, filename)
                if not os.path.exists(path):
                    print('---No such file!---')
                    continue
                filesize = os.stat(path).st_size
                fileinfo = {'filename': filename, 'filepath': filepath, 'filesize': filesize}
                # 数据封装，转为json格式
                filejson = json.dumps(fileinfo).encode('utf-8')
                long = len(filejson)
                # 报文格式：数据报首部4字节为发送数据大小
                pack_long = struct.pack('i', long)
                sk.send(pack_long)
                sk.send(filejson)
                # 只读模式
                with open(path, 'rb')as f:
                    while filesize:
                        if filesize >= buffer:
                            filedata = f.read(buffer)
                            sk.send(filedata)
                            filesize -= buffer
                        else:
                            filedata = f.read(filesize)
                            sk.send(filedata)
                            break

                show = '{0}\nUpload：{1}:\n{2}byte'.format(time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(time.time())), filename, filesize)
                print(show)
                # 返回成功信息
                print(sk.recv(buffer).decode('utf-8'))

            # 选择下载
            elif data == 'D':
                # 收到文件列表
                r = sk.recv(buffer).decode('utf-8')
                if operator.eq(r, ''):
                    print('×No downloadable files.×')
                    continue
                print(r)
                filename = input('Input the filename you want to download>>>')
                if not filename:
                    print('Can not empty!')
                    continue
                # 发送要下载的文件名
                sk.send(bytes(filename.encode('utf-8')))
                # 文件下载状态
                state = sk.recv(buffer).decode('utf-8')
                if state == 'No such file!!':
                    print(state)
                    os.chdir(os.path.abspath(os.path.dirname(os.getcwd())))
                    continue
                print(state)
                # 4字节的包：文件信息大小
                info = sk.recv(4)
                size = struct.unpack('i', info)[0]
                print(filename, size)

                data = sk.recv(size).decode('utf-8')

                # 先取得文件的绝对路径，然后得到文件目录
                path = os.path.dirname(os.path.abspath(__file__))
                path = os.path.join(path, 'tmp')
                os.chdir(path)
                with open(filename, 'w+', encoding='utf-8')as f:
                    f.write(data)
                print(data)
                os.chdir(os.path.abspath(os.path.dirname(os.getcwd())))

            # 选择命令行模式
        elif data == 'CMD':
            sk.send((data.encode('utf-8')))
            com = input('Input command-->')
            if not com:
                print('Can not empty!')

            sk.send(com.encode())
            res = sk.recv(8096)
            # 解开报头取出数据长度
            length = struct.unpack('i', res)[0]
            size = 0
            data = b''
            while size < length:
                data += sk.recv(buffer)
                size += len(data)
            print('Server command -->{0}'.format(data.decode('gbk')) + '\n')
        else:
            print('Invalid command!')

    sk.close()

if __name__ == '__main__':
    socket_client()
