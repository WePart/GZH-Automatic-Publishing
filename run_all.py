import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

def get_numbered_dirs():
    # 获取所有子目录
    dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    # 过滤出符合数字命名模式的目录并排序
    numbered_dirs = sorted([d for d in dirs if d.split('-')[0].isdigit()])
    return numbered_dirs

def show_dir_menu(dirs):
    print("\n可用的目录：")
    for i, dir_name in enumerate(dirs, 1):
        print(f"{i}. {dir_name}")
    print("0. 退出程序")

def get_python_files(directory):
    # 获取目录下所有的 .py 文件（排除 run_all.py）
    return sorted([f for f in os.listdir(directory) 
                  if f.endswith('.py') and f != 'run_all.py'])

def show_files_menu(files):
    print("\n当前目录下的Python文件：")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    print("\n提示：可以输入范围，如 '1-6' 表示运行1到6号文件，直接回车运行所有文件")

def run_single_file(file_info):
    directory, file = file_info
    print(f'开始运行: {file}')
    original_dir = os.getcwd()
    os.chdir(directory)
    
    # 创建进程
    process = subprocess.Popen(
        ['python', '-u', file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    print(f"\n--- {file} 的输出 ---")
    
    # 使用迭代器来读取输出
    for line in iter(process.stdout.readline, ''):
        print(line, end='', flush=True)
    
    # 读取错误输出
    for line in iter(process.stderr.readline, ''):
        print("错误:", line, end='', flush=True)
    
    # 等待进程结束
    process.wait()
    
    os.chdir(original_dir)
    return file

def run_python_files(directory, files_to_run):
    print(f"\n将按顺序运行以下文件：{', '.join(files_to_run)}")
    
    # 简化函数，因为输出已经在 run_single_file 中处理
    for file in files_to_run:
        run_single_file((directory, file))
        print("\n" + "="*50 + "\n")  # 添加分隔线

if __name__ == '__main__':
    while True:
        # 获取并显示目录列表
        numbered_dirs = get_numbered_dirs()
        if not numbered_dirs:
            print("错误：当前目录下没有找到符合格式的子目录")
            exit(1)
            
        show_dir_menu(numbered_dirs)
        
        # 获取用户选择
        try:
            choice = int(input("\n请选择要运行的目录编号（0退出）："))
            if choice == 0:
                print("程序已退出")
                break
            elif 1 <= choice <= len(numbered_dirs):
                selected_dir = numbered_dirs[choice - 1]
                print(f"\n已选择目录：{selected_dir}")
                
                # 获取并显示文件列表
                py_files = get_python_files(selected_dir)
                if not py_files:
                    print("该目录下没有可运行的Python文件")
                    continue
                    
                show_files_menu(py_files)
                
                # 获取文件范围选择
                choice = input("请选择要运行的文件范围：").strip()

                if not choice:  # 如果直接回车，执行所有文件
                    start_idx = 1
                    end_idx = len(py_files)
                elif '-' in choice:  # 处理范围输入
                    start_idx, end_idx = map(int, choice.split('-'))
                else:  # 处理单个数字输入
                    start_idx = end_idx = int(choice)

                if 1 <= start_idx <= end_idx <= len(py_files):
                    selected_files = py_files[start_idx-1:end_idx]
                    print(f"\n将运行以下文件：{', '.join(selected_files)}")
                    run_python_files(selected_dir, selected_files)
                else:
                    print("无效的文件范围，请重新选择")
            else:
                print("无效的选择，请重新输入")
        except ValueError:
            print("请输入有效的数字") 