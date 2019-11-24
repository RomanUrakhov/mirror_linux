# coding=utf-8
import datetime
import subprocess
import time

# создает файловую систему zfs в dir_path
def create(dir_path):
    ############################
    time.sleep(20)
    print(f"Task Create {dir_path}")
    return 1
    #############################
    # try:
    #     subprocess.check_call(["zfs", "create", dir_path])
    # except subprocess.CalledProcessError as e:
    #     return -1
    # return 0


# rsync выполняет синхронизацию с address_server в dir_path -> zstorage/test3
# v - увеличить уровень подробностей
# a - архивный режим
# H - сохранять жесткие ссылки
# z - сжимать поток передачи данных

def update(dir_path, address_server, args = "-vaHz"):
    ############################
    time.sleep(60)
    print(f"Task update args = {args}")
    return 1
    #############################
    # try:
    #     subprocess.check_call(["rsync", args, address_server, "/" + dir_path + "/"])
    # except subprocess.CalledProcessError as e:
    #     return -2
    # return 0


# create snapshot and delete last if count_snapshot >
def snapshot(dir_path, count_snapshot):
    ############################
    time.sleep(20)
    print(f"Task snapshot count_snaps = {count_snapshot}; dir = {dir_path}")
    return 1
    #############################
    # try:
    #     snapname = str(datetime.datetime.now())
    #     snapname = snapname.replace(' ', '_')
    #     subprocess.check_call(["zfs", "snapshot", dir_path + "@" + snapname])
    #
    #     # берем количество существующих dir_path
    #     isMore = "zfs list -H -t snapshot -o name -S creation -r " + dir_path + " | wc -l"
    #     # subprocess.call(isMore, shell=True)
    #
    #     # если их больше то удаляем
    #     if int(subprocess.check_output(isMore, shell=True)) > count_snapshot:
    #         delete = "zfs list -H -t snapshot -o name -S creation -r " + dir_path + " | tail -1 | xargs -n 1 zfs  destroy"
    #         subprocess.call(delete, shell=True)
    #         print("deleted")
    #
    # except subprocess.CalledProcessError as e:
    #     return -3
    #
    # return 0


def reset(dir_zfs):
    ############################
    time.sleep(20)
    print("Task reset")
    return 1
    #############################
    # # delete zfs file system
    # delete(dir_zfs)
    # # create zfs
    # create(dir_zfs)
    # return 0


def delete(dir_zfs):
    ############################
    time.sleep(20)
    print(f"Task delete dir= {dir_zfs}")
    return 1
    #############################
    # # delete zfs file system
    # try:
    #     subprocess.check_call(["zfs", "destroy", "-r", dir_zfs])
    # except subprocess.CalledProcessError as e:
    #     return -1
    # return 0