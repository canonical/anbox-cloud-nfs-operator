#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd
# See LICENSE file for licensing details.

import logging
import os

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus
from ops.framework import StoredState

import charms.operator_libs_linux.v0.apt as apt
import charms.operator_libs_linux.v1.systemd as systemd

logger = logging.getLogger(__name__)

NFS_BASE_UNIT_NAME = r'media-anbox\x2ddata'
NFS_MOUNT_UNIT_NAME = f"{NFS_BASE_UNIT_NAME}.mount"
REQUIRED_APT_PACKAGES = ['cachefilesd', 'nfs-common']
MOUNT_TARGET_PATH = '/media/anbox-data'


class NFSOperatorCharm(CharmBase):
    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.stop, self._on_stop)

        self.state.set_default(
            nfs_path=None,
            nfs_extra_options=None,
        )

    def _get_nfs_path(self):
        return self.model.config['nfs_path'] or None

    def _on_install(self, event):
        self._install_dependencies()
        self._setup_cachefilesd()

        extra_opts = self.model.config["nfs_extra_options"]
        self._render_mount_unit(self._get_nfs_path(),
                                MOUNT_TARGET_PATH, extra_opts)
        self.unit.status = ActiveStatus()

    def _on_stop(self, event):
        apt.remove_package(REQUIRED_APT_PACKAGES)

    def _on_config_changed(self, event):
        self._setup_cachefilesd()
        extra_opts = self.model.config["nfs_extra_options"]
        self._render_mount_unit(self._get_nfs_path(),
                                MOUNT_TARGET_PATH, extra_opts)

    def _install_dependencies(self):
        apt.update()
        apt.add_package(REQUIRED_APT_PACKAGES)

    def _setup_cachefilesd(self):
        brun = self.model.config["cachefilesd_brun"] or 10
        bcull = self.model.config["cachefilesd_bcull"] or 7
        bstop = self.model.config["cachefilesd_bstop"] or 3

        if not brun > bcull and not bcull > bstop:
            raise Exception("Invalid cachefilesd configuration")

        frun = self.model.config["cachefilesd_frun"] or 10
        fcull = self.model.config["cachefilesd_fcull"] or 7
        fstop = self.model.config["cachefilesd_fstop"] or 3

        if not frun > fcull and not fcull > fstop:
            raise Exception("Invalid cachefilesd configuration")

        defaults = """# DO NOT MODIFY - This file is managed by the Anbox Cloud NFS operator charm
RUN=yes
DAEMON_OPTS=
"""
        self._write_content('/etc/default/cachefilesd', defaults)

        config = f"""# DO NOT MODIFY - This file is managed by the Anbox Cloud NFS operator charm
dir /var/cache/fscache
tag anbox-cloud
brun {brun}%
bcull {bcull}%
bstop {bstop}%
frun {frun}%
fcull {fcull}%
fstop {fstop}%
"""
        self._write_content('/etc/cachefilesd.conf', config)

        systemd.service_restart('cachefilesd')

    def _write_content(self, path, content):
        if os.path.exists(path):
            os.remove(path)
        with open(os.open(path, os.O_CREAT | os.O_WRONLY, 0o644), 'w+') as f:
            f.write(content)

    def _get_unit_path(self, name):
        return f"/etc/systemd/system/{name}"

    def _remove_mount_unit(self, name):
        unit_path = self._get_unit_path(name)
        if os.path.exists(unit_path):
            systemd.serivce_stop(NFS_MOUNT_UNIT_NAME)
            os.remove(unit_path)

    def _render_mount_unit(self, path, target_path, extra_opts=None):
        if self.state.nfs_path == path and self.state.nfs_extra_options == extra_opts:
            return

        if not path:
            self._remove_mount_unit(NFS_MOUNT_UNIT_NAME)
            return

        if len(target_path) == 0:
            raise Exception("No target path for NFS mount given")

        unit_path = self._get_unit_path(NFS_MOUNT_UNIT_NAME)
        if os.path.exists(unit_path):
            systemd.service_stop(NFS_MOUNT_UNIT_NAME)

        mount_opts = "soft,async,fsc"
        if extra_opts and len(extra_opts) > 0:
            mount_opts += f",{extra_opts}"

        content = f"""# DO NOT MODIFY - This file is managed by the Anbox Cloud NFS operator charm
[Unit]
Description=NFS mount for {path}
After=network-online.target
Wants=network-online.target

[Mount]
Type=nfs
What={path}
Where={target_path}
Options={mount_opts}

[Install]
WantedBy=multi-user.target
"""

        self._write_content(unit_path, content)

        systemd.daemon_reload()
        systemd.service_resume(NFS_MOUNT_UNIT_NAME)
        systemd.service_start(NFS_MOUNT_UNIT_NAME)

        self.state.nfs_path = path
        self.state.nfs_extra_options = extra_opts


if __name__ == "__main__":  # pragma: nocover
    main(NFSOperatorCharm)
