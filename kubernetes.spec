#debuginfo not supported with Go
%global debug_package	%{nil}
%global import_path	github.com/GoogleCloudPlatform/kubernetes
%global commit		1c61486ec343246a81f62b4297671217c9576df7
%global shortcommit	%(c=%{commit}; echo ${c:0:7})

#binaries which should be called kube-*
%global prefixed_binaries proxy apiserver controller-manager scheduler
#binaries which should not be renamed at all
%global nonprefixed_binaries kubelet kubectl
#all of the above
%global binaries	%{prefixed_binaries} %{nonprefixed_binaries}

#I really need this, otherwise "version_ldflags=$(kube::version_ldflags)"
# does not work
%global _buildshell	/bin/bash
%global _checkshell	/bin/bash

Name:		kubernetes
Version:	0.4
Release:	0.8.git%{shortcommit}%{?dist}
Summary:	Container cluster management
License:	ASL 2.0
URL:		https://github.com/GoogleCloudPlatform/kubernetes
ExclusiveArch:	x86_64
Source0:	https://github.com/GoogleCloudPlatform/kubernetes/archive/%{commit}/kubernetes-%{shortcommit}.tar.gz

Patch1:		0001-remove-all-third-party-software.patch

%if 0%{?fedora} >= 21 || 0%{?rhel}
Requires:	docker
%else
Requires:	docker-io
%endif

Requires:	etcd
Requires:	cadvisor

Requires(pre):	shadow-utils

BuildRequires:	git
BuildRequires:	golang >= 1.2-7
BuildRequires:	systemd
BuildRequires:	golang-cover
BuildRequires:	etcd
BuildRequires:	golang(bitbucket.org/kardianos/osext)
BuildRequires:	golang(code.google.com/p/gcfg)
BuildRequires:	golang(code.google.com/p/goauth2)
BuildRequires:	golang(code.google.com/p/go.net/context)
BuildRequires:	golang(code.google.com/p/go.net/html)
BuildRequires:	golang(code.google.com/p/go.net/websocket)
BuildRequires:	golang(code.google.com/p/google-api-go-client)
BuildRequires:	golang(code.google.com/p/go-uuid)
BuildRequires:	golang(github.com/coreos/go-etcd/etcd)
BuildRequires:	golang(github.com/coreos/go-log/log)
BuildRequires:	golang(github.com/coreos/go-systemd)
BuildRequires:	golang(github.com/elazarl/go-bindata-assetfs)
BuildRequires:	golang(github.com/fsouza/go-dockerclient) > 0-0.6
BuildRequires:	golang(github.com/golang/glog)
BuildRequires:	golang(github.com/google/cadvisor)
BuildRequires:	golang(github.com/google/gofuzz)
BuildRequires:	golang(github.com/kr/text)
BuildRequires:	golang(github.com/mitchellh/goamz/aws)
BuildRequires:	golang(github.com/mitchellh/goamz/ec2)
BuildRequires:	golang(github.com/mitchellh/mapstructure)
BuildRequires:	golang(github.com/racker/perigee)
BuildRequires:	golang(github.com/rackspace/gophercloud)
BuildRequires:	golang(github.com/skratchdot/open-golang/open)
BuildRequires:	golang(github.com/spf13/cobra)
BuildRequires:	golang(github.com/spf13/pflag)
BuildRequires:	golang(github.com/stretchr/objx)
BuildRequires:	golang(github.com/stretchr/testify)
BuildRequires:	golang(github.com/tonnerre/golang-pretty)
BuildRequires:	golang(github.com/vaughan0/go-ini)
BuildRequires:	golang(gopkg.in/v1/yaml)


%description
%{summary}

%prep
%autosetup -Sgit -n %{name}-%{commit}

%build
export KUBE_GIT_COMMIT=%{commit}
export KUBE_GIT_TREE_STATE="dirty"
export KUBE_GIT_VERSION=v%{version}

export KUBE_EXTRA_GOPATH=%{gopath}
export KUBE_NO_GODEPS="true"

. hack/config-go.sh

kube::setup_go_environment

version_ldflags=$(kube::version_ldflags)

targets=($(kube::default_build_targets))
targets+=("cmd/integration")
binaries=($(kube::binaries_from_targets "${targets[@]}"))

for binary in ${binaries[@]}; do
  bin=$(basename "${binary}")
  echo "+++ Building ${bin}"
  go build -o "${KUBE_TARGET}/bin/${bin}" \
        "${goflags[@]:+${goflags[@]}}" \
        -ldflags "${version_ldflags}" \
        "${binary}"
done

%check
export KUBE_EXTRA_GOPATH=%{gopath}
export KUBE_NO_GODEPS="true"
export KUBE_NO_BUILD_INTEGRATION="true"
exit
echo "******Testing the commands*****"
hack/test-cmd.sh
# In Fedora 20 and RHEL7 the go cover tools isn't available correctly
%if 0%{?fedora} >= 21
echo "******Testing the go code******"
hack/test-go.sh
echo "******Testing integration******"
hack/test-integration.sh
%endif
echo "******Benchmarking kube********"
hack/benchmark-go.sh

%install
install -m 755 -d %{buildroot}%{_bindir}
for bin in %{prefixed_binaries}; do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 _output/go/bin/${bin} %{buildroot}%{_bindir}/kube-${bin}
done
for bin in %{nonprefixed_binaries}; do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 _output/go/bin/${bin} %{buildroot}%{_bindir}/${bin}
done

# install the bash completion
install -d -m 0755 %{buildroot}%{_datadir}/bash-completion/completions/
install -t %{buildroot}%{_datadir}/bash-completion/completions/ contrib/completions/bash/kubectl

# install config files
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}
install -m 644 -t %{buildroot}%{_sysconfdir}/%{name} contrib/init/systemd/environ/*

# install service files
install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 -t %{buildroot}%{_unitdir} contrib/init/systemd/*.service

# install manpages
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 docs/man/man1/* %{buildroot}%{_mandir}/man1

# install the place the kubelet defaults to put volumes
install -d %{buildroot}/var/lib/kubelet

%files
%doc README.md LICENSE CONTRIB.md CONTRIBUTING.md DESIGN.md
%{_mandir}/man1/*
%{_bindir}/kube-apiserver
%{_bindir}/kubectl
%{_bindir}/kube-controller-manager
%{_bindir}/kubelet
%{_bindir}/kube-proxy
%{_bindir}/kube-scheduler
%{_unitdir}/kube-apiserver.service
%{_unitdir}/kubelet.service
%{_unitdir}/kube-scheduler.service
%{_unitdir}/kube-controller-manager.service
%{_unitdir}/kube-proxy.service
%dir %{_sysconfdir}/%{name}
%{_datadir}/bash-completion/completions/kubectl
%dir /var/lib/kubelet
%config(noreplace) %{_sysconfdir}/%{name}/config
%config(noreplace) %{_sysconfdir}/%{name}/apiserver
%config(noreplace) %{_sysconfdir}/%{name}/controller-manager
%config(noreplace) %{_sysconfdir}/%{name}/proxy
%config(noreplace) %{_sysconfdir}/%{name}/kubelet
%config(noreplace) %{_sysconfdir}/%{name}/scheduler

%pre
getent group kube >/dev/null || groupadd -r kube
getent passwd kube >/dev/null || useradd -r -g kube -d / -s /sbin/nologin \
        -c "Kubernetes user" kube
%post
%systemd_post kube-apiserver kube-scheduler kube-controller-manager kubelet kube-proxy

%preun
%systemd_preun kube-apiserver kube-scheduler kube-controller-manager kubelet kube-proxy

%postun
%systemd_postun

%changelog
* Tue Oct 28 2014 Eric Paris <eparis@redhat.com - 0.4-0.8.git1c61486
- Bump to upstream 1c61486ec343246a81f62b4297671217c9576df7

* Mon Oct 27 2014 Eric Paris <eparis@redhat.com - 0.4-0.7.gitdc7e3d6
- Bump to upstream dc7e3d6601a89e9017ca9db42c09fd0ecb36bb36

* Fri Oct 24 2014 Eric Paris <eparis@redhat.com - 0.4-0.6.gite46af6e
- Bump to upstream e46af6e37f6e6965a63edb8eb8f115ae8ef41482

* Thu Oct 23 2014 Eric Paris <eparis@redhat.com - 0.4-0.5.git77d2815
- Bump to upstream 77d2815b86e9581393d7de4379759c536df89edc

* Wed Oct 22 2014 Eric Paris <eparis@redhat.com - 0.4-0.4.git97dd730
- Bump to upstream 97dd7302ac2c2b9458a9348462a614ebf394b1ed
- Use upstream kubectl bash completion instead of in-repo
- Fix systemd_post and systemd_preun since we are using upstream service files

* Tue Oct 21 2014 Eric Paris <eparis@redhat.com - 0.4-0.3.gite868642
- Bump to upstream e8686429c4aa63fc73401259c8818da168a7b85e

* Mon Oct 20 2014 Eric Paris <eparis@redhat.com - 0.4-0.2.gitd5377e4
- Bump to upstream d5377e4a394b4fc6e3088634729b538eac124b1b
- Use in tree systemd unit and Environment files
- Include kubectl bash completion from outside tree

* Fri Oct 17 2014 Eric Paris <eparis@redhat.com - 0.4-0.1.gitb011263
- Bump to upstream b01126322b826a15db06f6eeefeeb56dc06db7af
- This is a major non backward compatible change.

* Thu Oct 16 2014 Eric Paris <eparis@redhat.com> - 0.4-0.0.git4452163
- rebase to v0.4
- include man pages

* Tue Oct 14 2014 jchaloup <jchaloup@redhat.com> - 0.3-0.3.git98ac8e1
- create /var/lib/kubelet
- Use bash completions from upstream
- Bump to upstream 98ac8e178fcf1627399d659889bcb5fe25abdca4
- all by Eric Paris

* Mon Sep 29 2014 Jan Chaloupka <jchaloup@redhat.com> - 0.3-0.2.git88fdb65
- replace * with coresponding files
- remove dependency on gcc

* Wed Sep 24 2014 Eric Paris <eparis@redhat.com - 0.3-0.1.git88fdb65
- Bump to upstream 88fdb659bc44cf2d1895c03f8838d36f4d890796

* Tue Sep 23 2014 Eric Paris <eparis@redhat.com - 0.3-0.0.gitbab5082
- Bump to upstream bab5082a852218bb65aaacb91bdf599f9dd1b3ac

* Fri Sep 19 2014 Eric Paris <eparis@redhat.com - 0.2-0.10.git06316f4
- Bump to upstream 06316f486127697d5c2f5f4c82963dec272926cf

* Thu Sep 18 2014 Eric Paris <eparis@redhat.com - 0.2-0.9.gitf7a5ec3
- Bump to upstream f7a5ec3c36bd40cc2216c1da331ab647733769dd

* Wed Sep 17 2014 Eric Paris <eparis@redhat.com - 0.2-0.8.gitac8ee45
- Try to intelligently determine the deps

* Wed Sep 17 2014 Eric Paris <eparis@redhat.com - 0.2-0.7.gitac8ee45
- Bump to upstream ac8ee45f4fc4579b3ed65faafa618de9c0f8fb26

* Mon Sep 15 2014 Eric Paris <eparis@redhat.com - 0.2-0.5.git24b5b7e
- Bump to upstream 24b5b7e8d3a8af1eecf4db40c204e3c15ae955ba

* Thu Sep 11 2014 Eric Paris <eparis@redhat.com - 0.2-0.3.gitcc7999c
- Bump to upstream cc7999c00a40df21bd3b5e85ecea3b817377b231

* Wed Sep 10 2014 Eric Paris <eparis@redhat.com - 0.2-0.2.git60d4770
- Add bash completions

* Wed Sep 10 2014 Eric Paris <eparis@redhat.com - 0.2-0.1.git60d4770
- Bump to upstream 60d4770127d22e51c53e74ca94c3639702924bd2

* Mon Sep 08 2014 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1-0.4.git6ebe69a
- prefer autosetup instead of setup (revert setup change in 0-0.3.git)
https://fedoraproject.org/wiki/Autosetup_packaging_draft
- revert version number to 0.1

* Mon Sep 08 2014 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0-0.3.git6ebe69a
- gopath defined in golang package already
- package owns /etc/kubernetes
- bash dependency implicit
- keep buildroot/$RPM_BUILD_ROOT macros consistent
- replace with macros wherever possible
- set version, release and source tarball prep as per
https://fedoraproject.org/wiki/Packaging:SourceURL#Github

* Mon Sep 08 2014 Eric Paris <eparis@redhat.com>
- make services restart automatically on error

* Sat Sep 06 2014 Eric Paris <eparis@redhat.com - 0.1-0.1.0.git6ebe69a8
- Bump to upstream 6ebe69a8751508c11d0db4dceb8ecab0c2c7314a

* Wed Aug 13 2014 Eric Paris <eparis@redhat.com>
- update to upstream
- redo build to use project scripts
- use project scripts in %check
- rework deletion of third_party packages to easily detect changes
- run apiserver and controller-manager as non-root

* Mon Aug 11 2014 Adam Miller <maxamillion@redhat.com>
- update to upstream
- decouple the rest of third_party

* Thu Aug 7 2014 Eric Paris <eparis@redhat.com>
- update to head
- update package to include config files

* Wed Jul 16 2014 Colin Walters <walters@redhat.com>
- Initial package
