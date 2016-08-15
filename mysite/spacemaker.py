import os
import time
import datetime


def files_to_delete(folder):
    # list of files, most recently accessed first
    return sorted([ os.path.join(folder, file) for file in os.listdir(folder)], key=lambda filename: os.path.getatime(filename), reverse=True)


def shrink_folder_to(total_bytes, folder):
    file_list = files_to_delete(folder)
    removed_files = []
    current_size = sum([os.path.getsize(file) for file in file_list])
    while current_size > total_bytes:
        removed_file = file_list.pop()
        removed_size = os.path.getsize(removed_file)
        current_size -= removed_size
        removed_date = datetime.datetime.fromtimestamp(os.path.getatime(removed_file)).strftime('%Y-%m-%d %H:%M:%S.%f')
        removed_files.append((removed_file, removed_size//1024, removed_date))
        os.remove(removed_file)
    if removed_files:
        with open('cleanup_log.txt', 'a') as log:
            logtext = '[' + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f') + ']\n'
            for removed_file in removed_files:
                logtext+= 'Removed {0}, {1} KB, last accessed {2}\n'.format(*removed_file)
            log.write(logtext)


if __name__ == '__main__':
    shrink_folder_to(0, 'output')