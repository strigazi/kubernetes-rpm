# 1. create symlink to openshift binary in the local directory
# 2. set envs
# 3. run tests

########################
# SYMLINKS             #
########################

# run it in a directory of extracted kubernetes-master and kubernetes-unit-tests rpms
# or redine the following envs
export OC_BIN_PATH=${OC_BIN_PATH:-./usr/bin/openshift}
export K8S_HACK_DIR=${K8S_HACK_DIR:-./var/lib/kubernetes-unit-test}

#o#######################
# SYMLINKS             #
########################
# recreate symlink to kubectl
for binary in kubectl kubelet kube-proxy kube-controller-manager kube-scheduler kube-apiserver; do
        rm -f ./${binary}
        ln -s ${OC_BIN_PATH} ${binary}
done

########################
# ENVS                 #
########################


########################
# TESTS                #
########################
TEST_DIRECTORY=$(pwd)
pushd ${K8S_HACK_DIR}

export KUBE_OUTPUT_HOSTBIN=${KUBE_OUTPUT_HOSTBIN:-${TEST_DIRECTORY}}
./hack/test-cmd.sh

popd
