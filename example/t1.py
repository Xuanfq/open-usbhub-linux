import os
import pty
import select
import threading
import time

def handle_serial_io(master_fd, response="Echo: "):
    """处理来自伪TTY的输入并回显"""
    buffer = b''  # 用于存储未完成的行
    while True:
        try:
            # 使用 select 监听 master_fd 是否有可读数据
            rlist, _, _ = select.select([master_fd], [], [], 0.1)
            if master_fd in rlist:
                data = os.read(master_fd, 1024)
                if not data:
                    break
                
                buffer += data
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    input_str = line.decode('utf-8').strip()
                    if input_str:
                        print(f"Received from serial: {input_str}")
                        response_data = f"{response}{input_str}\n".encode('utf-8')
                        os.write(master_fd, response_data)
        except Exception as e:
            print(f"Error handling serial IO: {e}")
            break

def create_virtual_serial(response="Echo: "):
    """创建一个虚拟串口设备并与之交互"""
    # 创建伪TTY对
    master_fd, slave_fd = pty.openpty()
    virtual_serial_name = os.ttyname(slave_fd)  # 获取从设备名称（即虚拟串口）
    print(f"Virtual serial device created at: {virtual_serial_name}")

    # 启动一个新的线程来处理串口IO
    io_thread = threading.Thread(target=handle_serial_io, args=(master_fd, response), daemon=True)
    io_thread.start()

    return virtual_serial_name

if __name__ == '__main__':
    try:
        # 创建虚拟串口并获取其名字
        virtual_serial = create_virtual_serial("Echo: ")

        print("You can now connect to this virtual serial device using:")
        print(f"    screen {virtual_serial}  # 或者其他串口工具")
        print("Press Ctrl+A followed by K and then Y to exit screen.")

        # 主线程保持运行，等待用户终止程序
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCaught keyboard interrupt, exiting gracefully.")