# Synd
Synd(or Sync data) is a python app to synchronize file system between connected peers using <a href="https://en.wikipedia.org/wiki/Secure_copy">scp</a> protocol. It helps you to sync file as well as subfolder inside specified folder.

# Dependencies
1. Python(2.7.x)<br>
2. <a href="https://github.com/seb-m/pyinotify">pyinotify</a>(Synd works only on linux because pyinotify use linux inotify system call to detect changes in file system. Alternative watchdog).

### Public ssh Key
As scp protocol is using for file transmission so it requiure authentication for every file transfer. To get rid of entering password again and again use public ssh key authentication.<br>
https://www.youtube.com/watch?v=EuIYabZS3ow

# Getting Started
```
git clone git@github.com:dggs123/Synd
cd Synd
```

execute synd.py

```
python synd.py -ip <source ip address> -port <source port> -uname <source username> -synfolder <synchronized folder> -destip <destination ip> -destport <destination port>
```
Synchronized folder will automatically create in /home/username directory.

## ex:

### Machine 1(synd1)

```
python2.7 synd.py -ip 138.197.109.119 -port 8000 -uname synd1 -synfolder syndata -destip 174.138.63.97 -destport 8000
```

### Machine 2(synd2)

```
python2.7 synd.py -ip 174.138.63.97 -port 8000 -uname synd2 -synfolder syndata -destip 138.197.109.119 -destport 8000
```

# Demo
Both the machines are hosted on digital ocean(Ubantu 16.04.3 x64).

Connect to machine 1(synd1):
```
ssh synd1@138.197.109.119
Password: demosynd
Public ssh key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/aT+6zGzgIYW6fOwluc1Q71+Gx5DNUEXTxrQ8pJO9tz3klBrClZITjjjGvl6CYc+5S3xKDGFnrFUMEVzmQy7c8rboXAlGKhxU+JZJQ6csP+JimSI0CEcor0Zfxt4Dt8pyzWa+SvIdsn0v9p/3W8ltB13nh4sklJpPsxjcsMVbNZiS/tXXS1wiGEEiWhMnnLV+uGUzgzxnQJJjCm/6BzQHHppFu4pzlU9X44JAPaN+0Xwz3UezVLP19aBwWxm6ir8TYis3nW1+E5MwRr2JIobvnTQby+UjctKiQqMLazjcHli5ShOWR4QkP93yOFC5lXDJq6+T1q52c2LpEku3mp43 synd1@ubuntu-1gb-nyc3-02
```

Connect to machine 2(synd2):
```
ssh synd2@172.138.63.97
Password: demosynd
Public ssh Key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDJjsJUL4P60frmok4J759JzwPETa7z6mE3nHsuMxpWWdi9R8L6pujSyoKXxUBjncCIKw5qJu6VPr66Sw6PHv2QDifTxHuTnyVRrbRz+eOT3FTfV/u60BGboxI+SiXTsyiW8O3jpFKRSdLxup1art8C8BfVcyFV4VlTXU4LPKlrf4HBU1iCGVKh46rRZm73fbvu4kwiZ3DjXJLzxyqSX7jZqZw5IJCylZ4yR3FcrlYV+vgPQFV7ybirnTUq/G6q5yVXhr+KLoLp9umkrzDbeNkTU+V3zMpN06Z6+D4sBnNzQuCgIFW7YoKJkpM2WxgeNZCO26He+W4WaoIpq+aAf86B synd2@ubuntu-1gb-nyc3-01
```

In both the machines, folder 'syndata' inside user home directory is synchronized (server running in background using nohup command). Try creating file inside 'syndata'.<br>
##### For better performance use terminal to create, delete or modify files inside syndata. 

# App Logic
Synd is based on peer connection using xmlrpclib.

Machine 1(synd1)<br>
* Using pyinotify find the change in file system then notify Machine 2(synd2) using remote procedure call(rpc).

Machine 2(synd2)<br>
* pull the updated file using secure copy protocol(scp).
