import os
import sys
import logging
import base

logger = logging.getLogger(__name__)

class Sshfs(base.BaseCommand):
    def __init__(self, config, instance, remotedir=None):
        super(self.__class__, self).__init__(config, instance)
        self.remotedir = remotedir

    @property
    def command(self):
        cmd = 'sshfs {options} {destination}:{remotedir} {mountpoint}'
        return cmd.format(destination=self.destination,
                          remotedir=self.remotedir,
                          mountpoint=self.mountpoint,
                          options=self.options )

    @classmethod
    def mounts(cls, mount_root_dir):
        lines = [line.strip("\n").split(" ") for line in open("/etc/mtab", "r").readlines()]
        system_mounts = set([mp for src, mp, fs, opt, p1, p2 in lines if fs == "fuse.sshfs"])
        possible_owned_mounts = set([os.path.join(mount_root_dir, d) for d in os.listdir(mount_root_dir)])
        owned_mounts = system_mounts & possible_owned_mounts
        return list(owned_mounts)

    @property
    def is_mounted(self):
        return self.mountpoint in Sshfs.mounts(self.config.mount_root_dir)

    @property
    def mountpoint(self):
        return os.path.join(self.config.mount_root_dir, '%s@%s' % (self.instance.name, self.instance.address))

    def mount(self):
        if not self.remotedir:
            raise RuntimeError("No remotedir specified")

        if not os.path.exists(self.mountpoint):
            os.mkdir(self.mountpoint)

        if self.is_mounted:
            logger.warn("Already mounted at %s" % self.mountpoint)
            sys.exit(1)

        rc = os.system(self.command)
        if rc == 0:
            return True

        logger.error("Failed to mount instance {} at {}".format(self.instance, self.mountpoint))
        os.rmdir(mountpoint)
        return False

    def unmount(self, mountpoint=None):
        if not mountpoint:
            mountpoint = self.mountpoint

        if os.path.exists(mountpoint) and os.system("fusermount -u %s" % mountpoint) == 0:
            os.rmdir(mountpoint)
            return True
        return False
