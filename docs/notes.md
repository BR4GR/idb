# idb

## setup

## easy edditing

1. Generate an SSH key pair on your PC (if you don't have one):

  ```bash
  ssh-keygen -t ed25519
  ```

2. Copy the public key to your Raspberry Pi:

  ```bash
  ssh-copy-id username@192.168.101.155
  ```

3. Install SSHFS

  ```bash
  sudo pacman -S sshfs
  ```

4. Create a local mount point:

  ```bash
  mkdir ~/pi_project
  ```

5. mount the remote directory:

  ```bash
  sshfs pi@192.168.101.155:/home/username/ ~/pi_project -o reconnect,default_permissions
  ```

- pi@192.168.101.155: Your Raspberry Pi's username and IP address.
- /home/pi/: The directory on the Raspberry Pi you want to mount (e.g., your home directory on the Pi).
- ~/pi_project: The local mount point you just created.
- -o reconnect,default_permissions: Good options to add. reconnect tries to re-establish the connection if it drops. default_permissions tries to map permissions correctly.

6. now you can in the py create a file or clone a pi_project

```bash
cd pi_project

git clone git@github.com:BR4GR/idb.git

cd idb

nvim blinkatest.py
```
