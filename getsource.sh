#!/bin/sh

set -e

SPEC=kubernetes.spec

wget https://github.com/GoogleCloudPlatform/kubernetes/archive/$1/kubernetes-${1:0:7}.tar.gz

#put the git hash in there
sed -i -e "s/%global commit\t\t[[:xdigit:]]\{40\}/%global commit\t\t$1/" ${SPEC}

#increment the version number
rpmdev-bumpspec --comment="Bump to upstream ${1}" --userstring="Eric Paris <eparis@redhat.com" ${SPEC}

echo "****Don't forget to run: fedpkg new-sources kubernetes-${1:0:7}.tar.gz"
