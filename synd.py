import os
import re
import pyinotify
import time
import logging
import subprocess
import threading
import argparse
import xmlrpclib
import shutil

from SimpleXMLRPCServer import SimpleXMLRPCServer
from pyinotify import WatchManager, ProcessEvent

# Start logging
logger = logging.getLogger('synd')
handler = logging.StreamHandler()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

#Watch over files
class PyHandler(ProcessEvent):

    def __init__(self, mfiles, rfiles, pulledfiles, removedfiles):
        self.m_files = mfiles
        self.r_files = rfiles
        self.p_files = pulledfiles
        self.r_p_files = removedfiles

    def process_IN_CREATE(self, event):
        filename = os.path.join(event.path, event.name)
        if not self.p_files.__contains__(filename):
            self.m_files.add(filename)
            logger.info("Created file: %s" ,  filename)
        else:
            self.p_files.remove(filename)

    def process_IN_DELETE(self, event):
        filename = os.path.join(event.path, event.name)
        if not self.r_p_files.__contains__(filename):
            self.r_files.add(filename)
            logger.info("Removed file: %s" , filename)
        else:
            self.r_p_files.remove(filename)

        # clear modified files
        try:
            self.m_files.remove(filename)
        except KeyError:
            pass

    def process_IN_MODIFY(self, event):
        filename = os.path.join(event.path, event.name)
        if not self.p_files.__contains__(filename):
            self.m_files.add(filename)
            logger.info("Modified file: %s" , filename)
        else:
            self.p_files.remove(filename)

# Node class for peer to peer connection 
class Node(object):

    def __init__(self, ip, port, username, watch_dir, dest_ip, dest_port):
        self.ip = ip
        self.port = port
        self.username = username
        self.watch_dir = watch_dir
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.m_files = set()  # set of modified files
        self.r_files = set()  # set of removed files
        self.p_files = set()  # set of pulled files
        self.r_p_files = set()  # set of removed pulled files

    @staticmethod
    def get_dest_path(filename, dest_uname, dest_folder):
        user_dir_pattern = re.compile("/home/[^ ]*?/[^ ]*?/")
        if re.search(user_dir_pattern, filename):
            destpath = user_dir_pattern.sub("/home/%s/%s/" % (dest_uname, dest_folder), filename)
        logger.info("destpath %s", destpath)
        return destpath

    def pull_file(self, filename, source_uname, source_ip, dirc):
        """pull file 'filename' from the source"""
        my_file = Node.get_dest_path(filename, self.username, self.watch_dir)
        self.p_files.add(my_file)
        if not dirc:
            proc = subprocess.Popen(['scp', "%s@%s:%s" % (source_uname, source_ip, filename), my_file])
            return_status = proc.wait()
            print return_status
            logger.info("Post status %s", return_status)
        else:
            if not os.path.isdir(my_file):
                os.makedirs(my_file) 


    def remove_file(self, filename):
        """remove 'filename' from the file system"""
        my_file = Node.get_dest_path(filename, self.username, self.watch_dir)
        self.r_p_files.add(my_file)
        if not os.path.isdir(my_file):
            try:
                os.remove(my_file)
                logger.info("Removed File %s", my_file)
            except OSError as e:
                logger.info("Error Removing File %s", e)
        else:
            try:
                shutil.rmtree(my_file)
                logger.info("Removed Folder %s", my_file)
            except Exception as e:
                logger.info("Error Removing Folder %s", e)
            
    def start_server(self):
        # start sync file thread
        sync_thread = threading.Thread(target=self.sync_files)
        sync_thread.start()
        logger.info("Thread 'syncfiles' started")

        # start watch file thread
        watch_thread = threading.Thread(target=self.watch_files)
        watch_thread.start()
        logger.info("Thread 'watchfiles' started")
        
        # Starting Server
        server = SimpleXMLRPCServer(("0.0.0.0", self.port), allow_none =True)
        server.register_instance(self)
        server.register_introspection_functions()
        rpc_thread = threading.Thread(target=server.serve_forever)
        rpc_thread.start()
        logger.info("Started RPC server thread. Listening on port %s.", self.port)

    def sync_files(self):
        m_files = self.m_files
        r_files = self.r_files
        print "sync"
        while True:
            try:
                time.sleep(10)
                for filename in list(m_files):
                    print filename
                    # Push this modified file to the peer client using scp
                    dirc = os.path.isdir(filename)
                    proxy = xmlrpclib.ServerProxy("http://%s:%s/" % (self.dest_ip, self.dest_port), allow_none=True)
                    proxy.pull_file(filename, self.username, self.ip, dirc)
                    try:
                        m_files.remove(filename)
                    except KeyError:
                        pass
                for filename in list(r_files):
                    print filename
                    # removed file to the peer client
                    
                    proxy = xmlrpclib.ServerProxy("http://%s:%s/" % (self.dest_ip, self.dest_port), allow_none=True)
                    proxy.remove_file(filename)
                    try:
                        r_files.remove(filename)
                    except KeyError:
                        pass
            except KeyboardInterrupt:
                break

    def watch_files(self):
        wm = WatchManager()
        # watched events
        mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY
        notifier = pyinotify.Notifier(wm, PyHandler(self.m_files, self.r_files, self.p_files, self.r_p_files))

        wdd = wm.add_watch('/home/%s/%s' % (self.username, self.watch_dir), mask, rec=False, auto_add=True)
        while True:
            try:
                time.sleep(5)
                notifier.process_events()
                if notifier.check_events():
                    notifier.read_events()
            except KeyboardInterrupt:
                notifier.stop()
                break
        logger.info('%s' % self.m_files)
        print self.m_files

    def start(self):
        dirc = '/home/%s/%s' % (self.username, self.watch_dir)
        if not os.path.isdir(dirc):
            os.makedirs(dirc)
        self.start_server()

# This func called first
def main():
    # parser to take input from command line
    parser = argparse.ArgumentParser(
        description="""Synd""",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-ip', help='Ip address of this machine', required=True)

    parser.add_argument(
        '-port', help='Enter the port number', required=True)

    parser.add_argument(
        '-uname', help='Enter user name', required=True)

    parser.add_argument(
        '-synfolder', help='Specify the /home/username/[sync_folder]', required=True)

    parser.add_argument(
        '-destip', help='Ip of detination machine', required=True)

    parser.add_argument(
        '-destport', help='Port of detination machine', required=True)

    args = parser.parse_args()

    # create node instance
    node = Node(args.ip, int(args.port), args.uname, args.synfolder, args.destip, args.destport)

    node.start()

if __name__ == "__main__":
    main()
