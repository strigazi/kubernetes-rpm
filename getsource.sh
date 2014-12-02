#!/bin/sh

KUBE_GIT_COMMIT="$1"
KUBE_GIT_SHORT="${KUBE_GIT_COMMIT:0:7}"
KUBE_GIT_VERSION="$2"

set -o errexit
set -o nounset
set -o pipefail

SPEC=kubernetes.spec

curl -s -L https://github.com/GoogleCloudPlatform/kubernetes/archive/${KUBE_GIT_COMMIT}.tar.gz > kubernetes-${KUBE_GIT_SHORT}.tar.gz

since_tag=0
if [[ "${KUBE_GIT_VERSION}" =~ ^v([0-9]+)\.([0-9]+)\-([0-9]+)\-(.*)?$ ]]; then
  git_major=${BASH_REMATCH[1]}
  git_minor=${BASH_REMATCH[2]}
  since_tag=${BASH_REMATCH[3]}
# handle version like 0.4.2 (although we just ignore the .2 portion...)
elif [[ "${KUBE_GIT_VERSION}" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)\-([0-9]+)\-(.*)?$ ]]; then
  git_major=${BASH_REMATCH[1]}
  git_minor=${BASH_REMATCH[2]}
  since_tag=${BASH_REMATCH[4]}
fi

#put the git hash in as the commit
sed -i -e "s/%global commit\t\t[[:xdigit:]]\{40\}/%global commit\t\t${KUBE_GIT_COMMIT}/" ${SPEC}
#update the version with the latest tag
sed -i -e "s/Version:\t[[:digit:]]\+\.[[:digit:]]\++\?/Version:\t${git_major}.${git_minor}/" ${SPEC}
#update the release with since_tag
sed -i -e "s/Release:\t[[:digit:]]\+\.[[:digit:]]\+/Release:\t${since_tag}.0/" ${SPEC}
#update the git Version inside the built binaries
sed -i -e "s/export KUBE_GIT_VERSION=v.*/export KUBE_GIT_VERSION=${KUBE_GIT_VERSION}/" ${SPEC}

#increment the version number
./add-chglog --comment="Bump to upstream ${KUBE_GIT_COMMIT}" --userstring="Eric Paris <eparis@redhat.com>" ${SPEC}

fedpkg clog

echo "****Don't forget to run: fedpkg new-sources kubernetes-${KUBE_GIT_SHORT}.tar.gz"
