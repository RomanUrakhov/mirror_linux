import daemon
import daemon.pidfile
import argparse
import logging
import configparser
import os
import sys
import signal
import time
import threading
import queue
import subprocess
import psutil
from datetime import datetime

from app.models import Repository, QueueTask, Task
from playhouse.db_url import connect
import queries.repository
import queries.task

DAEMON_NAME = "MirrorManager"


class MirrorTask:
    def __init__(self, id, timeout):
        self.id = id  # repo id
        self.timeout = timeout


class WorkerThread:
    def __init__(self, config, logger, task_queue):
        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )
        self.tid = None

        self.config = config
        self.logger = logger
        self.task_queue = task_queue

        self.alive = False

    def start(self):
        self.alive = True
        self.thread.start()

    def stop(self):
        self.alive = False

    def join(self):
        self.thread.join()

    @staticmethod
    def __subprocess_run(*popenargs, input_=None, capture_output=False,
                         timeout=None, check=False, **kwargs):
        if input_ is not None:
            if kwargs.get('stdin') is not None:
                raise ValueError('stdin and input arguments may not both be used.')
            kwargs['stdin'] = subprocess.PIPE

        if capture_output:
            if kwargs.get('stdout') is not None or kwargs.get('stderr') is not None:
                raise ValueError('stdout and stderr arguments may not be used '
                                 'with capture_output.')
            kwargs['stdout'] = subprocess.PIPE
            kwargs['stderr'] = subprocess.PIPE

        with subprocess.Popen(*popenargs, **kwargs, start_new_session=True) as process:
            try:
                stdout, stderr = process.communicate(input_, timeout=timeout)
            except subprocess.TimeoutExpired:
                # process.kill()
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)

                # POSIX _communicate already populated the output so
                # far into the TimeoutExpired exception.
                process.wait()
                raise
            except:  # Including KeyboardInterrupt, communicate handled that.
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                # process.kill()
                # We don't call process.wait() as .__exit__ does that for us.
                raise
            retcode = process.poll()
            if check and retcode:
                raise subprocess.CalledProcessError(retcode, process.args,
                                                    output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)

    def __processing_task(self, task):
        try:
            self.logger.info(f'Thread: {self.tid}. Working on {task.id}')

            repo = Repository.get_by_id(task.id)
            # защита от двойного обновления (процесс обн. еще не закончился, а по расписанию наступил уже новый)
            already_in_queue = QueueTask.select().where(QueueTask.repository == repo)
            if already_in_queue:
                if already_in_queue.pid == os.getpid():
                    self.logger.warning(f'This repo is currently being updated')
                    return
                self.logger.warning(f'Repo info is outdated. Refreshing...')
                already_in_queue.delete_instance()
            QueueTask.create(repository=repo, pid=os.getpid())

            try:
                queries.task.write_task_status(repo=repo, msg="Updating repository")

                out = self.__subprocess_run(
                    args=['update_repo.py', task.id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=task.timeout,
                )

                queries.task.write_task_status(repo=repo, msg=(out.returncode, out.stdout[-20000:]))
                self.logger.info(f'Thread: {self.tid}. Finished {task.id} ({out.returncode})')
            except subprocess.TimeoutExpired as e:
                queries.task.write_task_status(repo=repo, msg="Timeout exception")
                queries.task.write_task_status(repo=repo, msg=e.output[-20000:])
                self.logger.warning(f'Thread: {self.tid}. Task {task.id} interrupted by timeout')
            finally:
                QueueTask.delete().where(QueueTask.repository == repo)
        except Exception as e:
            s = str(e)
            self.logger.warning(f'Thread: {self.tid}. Task {task.id} interrupted by exception: {s}')

    def run(self):
        self.tid = threading.get_ident()
        self.logger.info(f"Thread: {self.tid}. Start")

        while self.alive:
            task = self.task_queue.get()
            if self.alive:
                if task:
                    self.__processing_task(task)
                else:
                    self.alive = False
            self.task_queue.task_done()

        # db.close()
        self.logger.info(f"Thread: {self.tid}. End")


class MirrorDaemon:
    def __init__(self):
        self.args = None
        self.config = None

        self.logger = None

        self.context = None

        self.alive = False

        self.task_queue = queue.Queue()

        self.threads = []

    @staticmethod
    def __parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config', help='config file name', default='config.ini')
        parser.add_argument('-l', '--logfile', help='log file name', default='updater_daemon.log')
        parser.add_argument('-p', '--pidfile', help='pid file name', default=f"{os.getcwd()}/updater_daemon.pid")
        parser.add_argument('-t', '--thread', help='num threads', default='1')
        return parser.parse_args()

    @staticmethod
    def __setup_logger(logger_name, logfile=None):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s")
        if logfile:
            handler = logging.FileHandler(logfile)
        else:
            handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return handler, logger

    def __handle_shutdown(self, signum, frame):
        self.logger.debug(f"The daemon has been terminated by a signal: {(signal.Signals(signum)).name}")
        # Отправка нотификации завершения
        self.task_queue = queue.Queue()
        for t in self.threads:
            t.stop()
            self.task_queue.put(None)

        parent = psutil.Process(os.getpid())
        for child in parent.children(recursive=True):
            child.kill()
        sys.exit(0)

    def __handle_graceful_shutdown(self, signum, frame):
        self.logger.debug(f"The daemon has been graceful shutdown by a signal: {(signal.Signals(signum)).name}")
        self.alive = False

    def __run(self):
        num_thread = self.config['daemon'].getint('thread', self.args.thread)
        if num_thread < 1:
            num_thread = 1
        # create new process group, become its leader
        # os.setpgrp()
        # Запуск рабочих потоков
        for idx in range(num_thread):
            t = WorkerThread(self.config, self.logger, self.task_queue)
            self.threads.append(t)
            t.start()

        db = connect(self.config['database'].get('database_url'))
        db.connect(reuse_if_open=True)
        db.bind([Repository])

        while self.alive:
            self.logger.info("The daemon is still working")
            # репы для обновления или у которых init = False
            repos_to_update = Repository.select().where(
                (Repository.schedule_next_update <= datetime.now()) |
                (not Repository.mirror_init)
            ).order_by(Repository.schedule_next_update)

            # определяем дату следующей обновы
            for repo in repos_to_update:
                queries.repository.set_next_update_date(repo)

            # send thirty task requests to the worker
            # Отмена тасков не нужна, так как таймаут таска расчитывается
            # на основе расписания и таск живет не дольше таймаута.

            # определяем timeout и заполняем task_queue
            for repo in repos_to_update:
                timeout = (repo.schedule_next_update - datetime.now()).total_seconds()
                self.task_queue.put(MirrorTask(repo.get_id(), timeout))
            time.sleep(60)

        db.close()
        # Отправка нотификации завершения:
        for _ in self.threads:
            self.task_queue.put(None)
        # block until all daemon are done
        self.task_queue.join()
        # Завершение потоков
        for t in self.threads:
            t.join()
        self.threads = []
        # Демон завершился.
        self.logger.info("The daemon has been stopped")

    def main(self):
        # Получаем аргументы запуска скрипта
        self.args = self.__parse_args()
        # читаем файл конфига
        self.config = configparser.ConfigParser()
        self.config.read(self.args.config)
        # настраиваем логер
        # если в кофиге нет опции с именем logfile то используется аргумент -l вызова скрипта
        handler, self.logger = self.__setup_logger(DAEMON_NAME, self.config['daemon'].get('logfile', self.args.logfile))
        # Демон жив!
        self.alive = True
        # настраиваем контекст демона
        self.context = daemon.DaemonContext(
            working_directory=os.getcwd(),
            pidfile=daemon.pidfile.PIDLockFile(self.config['daemon'].get('pidfile', self.args.pidfile)),
            files_preserve=[
                handler.stream,
            ],
            signal_map={
                signal.SIGTERM: self.__handle_shutdown,
                signal.SIGINT: self.__handle_shutdown,
                signal.SIGQUIT: self.__handle_graceful_shutdown,  # Плавное завершение
            },
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        try:
            with self.context:
                self.logger.debug("The daemon has been started")
                self.__run()  # main activities
        except Exception as e:
            self.logger.error(str(e))
            self.logger.info("The daemon has been interrupted due to an error")


if __name__ == '__main__':
    updater_daemon = MirrorDaemon()
    updater_daemon.main()
