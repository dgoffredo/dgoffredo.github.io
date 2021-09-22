Turn an Old Laptop into a Server
================================
Over the years I've garnered a collection of somewhat broken old laptops.  One
has a broken keyboard and no battery.  Another has a faulty SSD and a flaky
motherboard.  Both are slow when running modern systems.

For general computing, though, old laptops have some advantages:

- cheap (free, in my case)
- built-in monitor (if it works)
- built-in keyboard (if it works)
- battery power backup (if it works)
- built-in networking, GPU, camera, etc.
- designed for low power consumption
- flat form factor (when the lid is closed)

If you have an old laptop lying around that you'd like to turn into a home
Linux server that you control over ssh, here's how I set it up.

Linux USB installer
-------------------
Download an `.iso` file of your favorite Debian-based Linux distribution.
Ubuntu Server is a tempting choice, but if your laptop lacks a wired ethernet
card (like my most recent one), then the server distribution might not have
your wireless drivers.  Here be dragons.

Instead, we'll install a "desktop" flavored distribution and strip it down
afterward.

I used [Ubuntu Desktop 20.04.3][1] and flashed it onto a 32 GB USB flash drive
using [Startup Disk Creator][2].

Configure BIOS on old laptop
----------------------------
You need to tell the laptop to boot from the USB flash drive.  How to do this
will depend on the specific laptop, but it will involve one or more of the
following:

- pressing a special key during boot to enter the BIOS configuration menu
- disabling "Secure Boot"
- prioritizing "legacy" boot over UEFI boot
- making sure that the USB drive is first in the legacy and/or UEFI boot order
- save and exit BIOS configuration menu

With luck, the next boot will start some GUI/shell for the Linux distribution's
installer.

On the old laptop
-------------
Install the Linux distribution.  To keep things simple, I configure the main
user to have the same name as the main user on my primary computer ("david").
I like short names for the to-be server (e.g. "lenovo" for my old Yoga 2).

Once that's done and you've restarted the computer without the USB flash drive
and verified that it boots the system you installed, you're ready to strip it down.

Our first order of business is installing an SSH server so that you can
configure the computer remotely.  For example, I have mine set up with the lid
closed on a shelf somewhere.  _Don't close the lid yet, though_.
```console
$ sudo apt update
$ sudo apt install -y openssh-server
$ sudo apt upgrade -y
```

Now you can connect to the laptop remotely over ssh (see below).  Keep the lid
open, though, so that the laptop doesn't sleep.  We'll change that later.

On your real computer
---------------------
Switch to your favorite computer for computing and connect to your
soon-to-be-server laptop.  You can use the laptop's local IP address or
hostname (if it advertises one).  In my case, my user name is `david`
and the laptop's name is `lenovo`, so:
```console
$ ssh david@lenovo

david@lenovo $ echo 'we are now remoted into the laptop'
we are now remoted into the laptop
```
It will ask you for a password, and possibly multiple confirmations.  The
password is whatever you configured for the user (`david`) on the laptop.

The remaining commands in this section are to be run on the soon-to-be-server
laptop, over your ssh connection.  I'll use the shell prompt `david@lenovo $ `
to remind you.

Over ssh
--------
### Configure non-graphical boot
If I happen to have the lid open when the laptop boots, I don't want to see
a splash screen.  I want to see Linux's log, and then `systemd`'s once `init`
starts.  Here's how:
```console
david@lenovo $ sudo vi /etc/default/grub
```
That file might have a variable whose value is set to `"quiet splash"` or
similar.  If so, remove "quiet" and "splash," e.g. so that value is `""`.

Save and exit.  Then, regenerate the bootloader with the modified configuration:
```console
david@lenovo $ sudo update-grub
```

Now change the "run level" to the non-graphical one: 
```console
david@lenovo $ sudo systemctl enable multi-user.target
david@lenovo $ sudo systemctl set-default multi-user.target
```

Now your desktop Linux will feel more like a server.

### Closing the laptop lid does _nothing_
Lid open/close events from the hardware are handled by the login service.
Let's configure the handlers to ignore the events, rather than whatever they do
by default:
```console
david@lenovo $ sudo vi /etc/systemd/logind.conf
```
That file will have commented-out lines beginning with `HandleLid`, e.g.
```shell
#HandleLidSwitch=suspend
#HandleLidSwitchExternalPower=suspend
#HandleLidSwitchDocked=ignore
```
Uncomment them and change their values to `ignore`, e.g.
```shell
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
```
Save and exit.

Then restart the service to pick up the changes:
```console
david@lenovo $ sudo service systemd-logind restart
```

Now you can close the lid on the laptop, and nothing will happen.

### Authorize your public ssh key on the server
It's a pain to type my password every time I want to connect to the server.
The ssh server supports a per-user allow list of public keys to permit
without falling back to password authentication.  That file probably does not
yet exist on the server, so let's copy the contents of our public key to that
file on the server.

My public key is called `~/.ssh/id_ed25519.pub`.  Yours might have a different
name.

```console
david@lenovo $ mkdir ~/.ssh
```

Run this next command on your real computer, not on the server.
```console
$ scp ~/.ssh/id_ed25519.pub david@lenovo:/home/david/.ssh/authorized_keys
```

Now you can connect to the server without a password.
```console
$ ssh lenovo

david@lenovo $
```

Profit
------
Congrats, you now have a server in your house, you budding sysadmin, you.

My next steps are usually to:

- Install [git][6] so I can pull various projects.
- Install [nginx][3] and configure it to expose various projects.
- Set up a static local IP allocation for the server in my router.
- Set up port forwarding for HTTP, HTTPS, and ssh (on an alternative port).
    - If you expose ssh, be sure to harden the configuration.  No root, no
      password, max retries, etc.
- Install [certbot][4] and get HTTPS working with nginx.
- Set up [cron][5] jobs to do stuff (`crontab -e`).
    - For example, dynamic DNS to update the DNS records of your websites when
      your ISP changes your public IP address.

Happy hacking.

![laptop server](laptop.svg)

[1]: https://ubuntu.com/download/desktop/thank-you?version=20.04.3&architecture=amd64
[2]: https://en.wikipedia.org/wiki/Startup_Disk_Creator
[3]: https://nginx.org
[4]: https://certbot.eff.org/
[5]: https://en.wikipedia.org/wiki/Cron
[6]: https://git-scm.com/
