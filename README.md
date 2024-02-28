# Anbox Cloud NFS operator

## Description

The Anbox Cloud NFS operator charm allows providing additional storage to LXD
nodes via NFS. This is intended to be used to provide additional shared data
to Anbox containers, e.g. game assets.

Current features:

* Supports two modes to mount an NFS path, namely `nfs` and `efs`
* TLS support with EFS

## Usage

### Basic Usage

This operator is a subordinate charm and attaches itself to a principal charm.
To deploy the charm using its default configuration:

```shell
juju deploy anbox-cloud-nfs
```

To mount a basic network path use the following config:

```yaml
applications:
  nfs-op:
    charm: anbox-cloud-nfs
    channel: stable
    options:
      mount_type: nfs
      nfs_path: <host_address_ip_or_domain>:/
```

### Use EFS filesystem on AWS without TLS

> Note: This feature has been introduced recently. So if you are
> running an older version of the charm, please upgrade the charm using
> `juju refresh anbox-cloud-nfs --channel latest/stable`.

Using this feature requires the user to provide the charm with a debian package
named [aws-efs-utils](https://docs.aws.amazon.com/efs/latest/ug/installing-amazon-efs-utils.html#installing-other-distro)

```shell
juju deploy anbox-cloud-nfs --resource amazon-efs-utils-deb=<path_to_the_debian_package>
```

To mount an EFS filesystem on the machine using this charm, the `mount_type`
should be set to `efs`.

From shell:
```shell
juju config anbox-cloud-nfs mount_type=efs
```

In a bundle:
```yaml
applications:
  nfs-op:
    charm: anbox-cloud-nfs
    channel: latest/stable
    options:
      mount_type: efs
      nfs_path: <efs_id>:/
```

### Using EFS with TLS

To use the EFS mount with TLS, the config option for `nfs_extra_options` must be
set to `tls`.

```shell
juju config anbox-cloud-nfs nfs_extra_options=tls
```

> Note: While setting up EFS mounts please make sure the security groups are
> correctly setup for the EFS volume. For information on setting the security
> groups, please follow [this](https://docs.aws.amazon.com/efs/latest/ug/accessing-fs-create-security-groups.html)
> guide.

## Integrations (Relations)

Supported [relations](https://juju.is/docs/olm/relations):

#### `juju-info` interface:

The NFS Operator supports a `juju-info` interface to allow clients to connect
to the subordinate charm.

```yaml
provides:
      juju-info:
          interface: juju-info
```

juju v2.x:

```shell
juju relate anbox-cloud-nfs application
```

juju v3.x

```shell
juju integrate anbox-cloud-nfs application
```

To remove a relation:

```shell
juju remove-relation anbox-cloud-nfs application
```

## Security
Security issues in the Operator can be reported through [LaunchPad](https://wiki.ubuntu.com/DebuggingSecurity#How%20to%20File) on the [Anbox Cloud](https://bugs.launchpad.net/anbox-cloud) project. Please do not file GitHub issues about security issues.

## Contributing
Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this charm following best practice guidelines, and [CONTRIBUTING.md](https://github.com/canonical/anbox-cloud-nfs-operator/blob/main/CONTRIBUTING.md) for developer guidance.

## License
The Charmed Operator is distributed under the Apache Software License, version 2.0.
