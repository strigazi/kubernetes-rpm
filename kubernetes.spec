#debuginfo not supported with Go
%global debug_package	%{nil}
%global import_path	github.com/GoogleCloudPlatform/kubernetes
%global commit		5ef34bf52311901b997119cc49eff944c610081b
%global shortcommit	%(c=%{commit}; echo ${c:0:7})

#I really need this, otherwise "version_ldflags=$(kube::version_ldflags)"
# does not work
%global _buildshell	/bin/bash
%global _checkshell	/bin/bash

Name:		kubernetes
Version:	0.6
Release:	297.0.git%{shortcommit}%{?dist}
Summary:	Container cluster management
License:	ASL 2.0
URL:		https://github.com/GoogleCloudPlatform/kubernetes
ExclusiveArch:	x86_64
Source0:	https://github.com/GoogleCloudPlatform/kubernetes/archive/%{commit}/kubernetes-%{shortcommit}.tar.gz

%if 0%{?fedora}
Patch1:		0001-remove-all-third-party-software.patch
%endif

%if 0%{?fedora} >= 21 || 0%{?rhel}
Requires:	docker
%else
Requires:	docker-io
%endif

Requires:	etcd

Requires(pre):	shadow-utils

BuildRequires:	git
BuildRequires:	golang >= 1.2-7
BuildRequires:	systemd
BuildRequires:	etcd

%if 0%{?fedora}
# needed for go cover.  Not available in RHEL/CentOS (available in Fedora/EPEL)
BuildRequires:	golang-cover

BuildRequires:	golang(code.google.com/p/gcfg)
BuildRequires:	golang(code.google.com/p/goauth2)
BuildRequires:	golang(code.google.com/p/google-api-go-client) > 0-0.3
BuildRequires:	golang(code.google.com/p/go-uuid)
BuildRequires:	golang(github.com/coreos/go-etcd/etcd)
BuildRequires:	golang(github.com/davecgh/go-spew/spew)
BuildRequires:	golang(github.com/elazarl/go-bindata-assetfs)
BuildRequires:	golang(github.com/emicklei/go-restful)
BuildRequires:	golang(github.com/fsouza/go-dockerclient) > 0-0.6
BuildRequires:	golang(github.com/ghodss/yaml)
BuildRequires:	golang(github.com/golang/glog)
BuildRequires:	golang(github.com/google/cadvisor) >= 0.6.2
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
BuildRequires:	golang(golang.org/x/net/context)
BuildRequires:	golang(golang.org/x/net/html)
BuildRequires:	golang(golang.org/x/net/websocket)
BuildRequires:	golang(gopkg.in/v2/yaml)
%endif

%description
%{summary}

%prep
%autosetup -Sgit -n %{name}-%{commit}

%build
export KUBE_GIT_TREE_STATE="clean"
export KUBE_GIT_COMMIT=%{commit}
export KUBE_GIT_VERSION=v0.6.0-297-g5ef34bf5231190

%if 0%{?fedora}
export KUBE_GIT_TREE_STATE="dirty"
export KUBE_EXTRA_GOPATH=%{gopath}
export KUBE_NO_GODEPS="true"
%endif

hack/build-go.sh --use_go_build

%check
%if 0%{?fedora}
export KUBE_EXTRA_GOPATH=%{gopath}
export KUBE_NO_GODEPS="true"
%endif

echo "******Testing the commands*****"
hack/test-cmd.sh
echo "******Benchmarking kube********"
hack/benchmark-go.sh

# In Fedora 20 and RHEL7 the go cover tools isn't available correctly
%if 0%{?fedora} >= 21
echo "******Testing the go code******"
hack/test-go.sh
echo "******Testing integration******"
hack/test-integration.sh --use_go_build
%endif

%install
. hack/lib/init.sh
kube::golang::setup_env

output_path="${KUBE_OUTPUT_BINPATH}/$(kube::golang::current_platform)"

binaries=(kube-apiserver kube-controller-manager kube-scheduler kube-proxy kubelet kubectl)
install -m 755 -d %{buildroot}%{_bindir}
for bin in "${binaries[@]}"; do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 -t %{buildroot}%{_bindir} ${output_path}/${bin}
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
* Mon Dec 15 2014 Eric Paris <eparis@redhat.com> - 0.6-297.0.git5ef34bf
- Bump to upstream 5ef34bf52311901b997119cc49eff944c610081b

* Wed Dec 03 2014 Eric Paris <eparis@redhat.com>
- Replace patch to use old googlecode/go.net/ with BuildRequires on golang.org/x/net/

* Tue Dec 02 2014 Eric Paris <eparis@redhat.com> - 0.6-4.0.git993ef88
- Bump to upstream 993ef88eec9012b221f79abe8f2932ee97997d28

* Mon Dec 01 2014 Eric Paris <eparis@redhat.com> - 0.5-235.0.git6aabd98
- Bump to upstream 6aabd9804fb75764b70e9172774002d4febcae34

* Wed Nov 26 2014 Eric Paris <eparis@redhat.com> - 0.5-210.0.gitff1e9f4
- Bump to upstream ff1e9f4c191342c24974c030e82aceaff8ea9c24

* Tue Nov 25 2014 Eric Paris <eparis@redhat.com> - 0.5-174.0.git64e07f7
- Bump to upstream 64e07f7fe03d8692c685b09770c45f364967a119

* Mon Nov 24 2014 Eric Paris <eparis@redhat.com> - 0.5-125.0.git162e498
- Bump to upstream 162e4983b947d2f6f858ca7607869d70627f5dff

* Fri Nov 21 2014 Eric Paris <eparis@redhat.com> - 0.5-105.0.git3f74a1e
- Bump to upstream 3f74a1e9f56b3c3502762930c0c551ccab0557ea

* Thu Nov 20 2014 Eric Paris <eparis@redhat.com> - 0.5-65.0.gitc6158b8
- Bump to upstream c6158b8aa9c40fbf1732650a8611429536466b21
- include go-restful build requirement

* Tue Nov 18 2014 Eric Paris <eparis@redhat.com> - 0.5-14.0.gitdf0981b
- Bump to upstream df0981bc01c5782ad30fc45cb6f510f365737fc1

* Tue Nov 11 2014 Eric Paris <eparis@redhat.com> - 0.4-680.0.git30fcf24
- Bump to upstream 30fcf241312f6d0767c7d9305b4c462f1655f790

* Mon Nov 10 2014 Eric Paris <eparis@redhat.com> - 0.4-633.0.git6c70227
- Bump to upstream 6c70227a2eccc23966d32ea6d558ee05df46e400

* Fri Nov 07 2014 Eric Paris <eparis@redhat.com> - 0.4-595.0.gitb695650
- Bump to upstream b6956506fa2682afa93770a58ea8c7ba4b4caec1

* Thu Nov 06 2014 Eric Paris <eparis@redhat.com> - 0.4-567.0.git3b1ef73
- Bump to upstream 3b1ef739d1fb32a822a22216fb965e22cdd28e7f

* Thu Nov 06 2014 Eric Paris <eparis@redhat.com> - 0.4-561.0.git06633bf
- Bump to upstream 06633bf4cdc1ebd4fc848f85025e14a794b017b4
- Make spec file more RHEL/CentOS friendly

* Tue Nov 04 2014 Eric Paris <eparis@redhat.com - 0.4-510.0.git5a649f2
- Bump to upstream 5a649f2b9360a756fc8124897d3453a5fa9473a6

* Mon Nov 03 2014 Eric Paris <eparis@redhat.com - 0.4-477.0.gita4abafe
- Bump to upstream a4abafea02babc529c9b5b9c825ba0bb3eec74c6

* Mon Nov 03 2014 Eric Paris <eparis@redhat.com - 0.4-453.0.git808be2d
- Bump to upstream 808be2d13b7bf14a3cf6985bc7c9d02f48a3d1e0
- Includes upstream change to remove --machines from the APIServer
- Port to new build system
- Start running %check tests again

* Fri Oct 31 2014 Eric Paris <eparis@redhat.com - 0.4+-426.0.gita18cdac
- Bump to upstream a18cdac616962a2c486feb22afa3538fc3cf3a3a

* Thu Oct 30 2014 Eric Paris <eparis@redhat.com - 0.4+-397.0.git78df011
- Bump to upstream 78df01172af5cc132b7276afb668d31e91e61c11

* Wed Oct 29 2014 Eric Paris <eparis@redhat.com - 0.4+-0.9.git8e1d416
- Bump to upstream 8e1d41670783cb75cf0c5088f199961a7d8e05e5

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
