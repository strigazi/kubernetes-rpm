#!/bin/sh

GIT_COMMIT="$1"
GIT_SHORT="${GIT_COMMIT:0:7}"
GIT_VERSION="$2"

set -o errexit
set -o nounset
set -o pipefail

NAME=kubernetes
SPEC=${NAME}.spec

curl -s -L https://github.com/GoogleCloudPlatform/${NAME}/archive/${GIT_COMMIT}.tar.gz > ${NAME}-${GIT_SHORT}.tar.gz

since_tag=0
if [[ "${GIT_VERSION}" =~ ^v([0-9]+)\.([0-9]+)\-([0-9]+)\-(.*)?$ ]]; then
  git_major=${BASH_REMATCH[1]}
  git_minor=${BASH_REMATCH[2]}
  version="${git_major}.${git_minor}"
  since_tag=${BASH_REMATCH[3]}
# handle version like 0.4.2 (although we just ignore the .2 portion...)
elif [[ "${GIT_VERSION}" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)\-([0-9]+)\-(.*)?$ ]]; then
  git_major=${BASH_REMATCH[1]}
  git_minor=${BASH_REMATCH[2]}
  git_really_minor=${BASH_REMATCH[3]}
  version="${git_major}.${git_minor}.${git_really_minor}"
  since_tag=${BASH_REMATCH[4]}
fi


#put the git hash in as the commit
sed -i -e "s/%global commit\t\t[[:xdigit:]]\{40\}/%global commit\t\t${GIT_COMMIT}/" ${SPEC}
#update the version with the latest tag
sed -i -e "s/Version:\t[[:digit:]]\+\.[[:digit:]]\+\(\.[[:digit:]]\+\)\?/Version:\t${version}/" ${SPEC}
#update the release with since_tag
sed -i -e "s/Release:\t[[:digit:]]\+\.[[:digit:]]\+/Release:\t${since_tag}.0/" ${SPEC}
#update the git Version inside the built binaries
sed -i -e "s/export KUBE_GIT_VERSION=v.*/export KUBE_GIT_VERSION=${GIT_VERSION}/" ${SPEC}

#increment the version number
./add-chglog --comment="Bump to upstream ${GIT_COMMIT}" --userstring="Eric Paris <eparis@redhat.com>" ${SPEC}

fedpkg clog

echo "****Don't forget to run: fedpkg new-sources ${NAME}-${GIT_SHORT}.tar.gz"
