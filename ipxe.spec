# Resulting binary formats we want from iPXE
%global formats rom

# PCI IDs (vendor,product) of the ROMS we want for QEMU
#
#    pcnet32:	0x1022 0x2000
#   ne2k_pci:	0x10ec 0x8029
#      e1000:	0x8086 0x100e
#    rtl8139:	0x10ec 0x8139
# virtio-net:	0x1af4 0x1000
%global qemuroms 10222000 10ec8029 8086100e 10ec8139 1af41000

# We only build the ROMs if on an x86 build host. The resulting
# binary RPM will be noarch, so other archs will still be able
# to use the binary ROMs
%global buildarches %{ix86} x86_64

# debugging firmwares does not goes the same way as a normal program.
# moreover, all architectures providing debuginfo for a single noarch
# package is currently clashing in koji, so don't bother.
%global debug_package %{nil}

# Upstream don't do "releases" :-( So we're going to use the date
# as the version, and a GIT hash as the release. Generate new GIT
# snapshots using the folowing commands:
#
# $ hash=`git log -1 --format='%h'`
# $ date=`date '+%Y%m%d'`
# $ git archive --output ipxe-${date}-git${hash}.tar.gz --prefix ipxe-${date}-git${hash}/ ${hash}
#
# And then change these two:

%global date 20120328
%global hash aac9718

Summary:	A network boot loader
Name:		ipxe
Version:	1.0.0
Release:	0.git.%{date}
Group:		System/Configuration/Boot and Init 
License:	GPLv2 and BSD
Url:		http://ipxe.org/
Source0:	%{name}-%{date}-git%{hash}.tar.gz
Source1:	USAGE
Patch1:		%{name}-banner-timeout.patch

%ifarch %{buildarches}
BuildRequires:	mkisofs
BuildRequires:	mtools
BuildRequires:	perl
BuildRequires:	syslinux
Obsoletes:	gpxe <= 1.0.1

%description
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

%package bootimgs
Summary:	Network boot loader images in bootable USB, CD, floppy and GRUB formats
Group:		Emulators
BuildArch:	noarch
Obsoletes:	gpxe-bootimgs <= 1.0.1

%description bootimgs
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

This package contains the iPXE boot images in USB, CD, floppy, and PXE
UNDI formats.

%package roms
Summary:	Network boot loader roms in .rom format
Group:		Emulators
Requires:	%{name}-roms-qemu = %{version}-%{release}
BuildArch:	noarch
Obsoletes:	gpxe-roms <= 1.0.1

%description roms
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

This package contains the iPXE roms in .rom format.

%package roms-qemu
Summary:	Network boot loader roms supported by QEMU, .rom format
Group:		Emulators
BuildArch:	noarch
Obsoletes:	gpxe-roms-qemu <= 1.0.1

%description roms-qemu
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

This package contains the iPXE ROMs for devices emulated by QEMU, in
.rom format.
%endif

%prep
%setup -qn %{name}-%{date}-git%{hash}
%autopatch -p1
cp -a %{SOURCE1} .

%build
mkdir -p bfd
ln -s %{_bindir}/ld.bfd bfd/ld
export PATH=$PWD/bfd:$PATH

%ifarch %{buildarches}
ISOLINUX_BIN=/usr/lib/syslinux/isolinux.bin
cd src
# ath9k drivers are too big for an Option ROM
rm -rf drivers/net/ath/ath9k

make \
	bin/undionly.kpxe \
	bin/ipxe.{dsk,iso,usb,lkrn} \
	allroms \
        ISOLINUX_BIN=${ISOLINUX_BIN} NO_WERROR=1 V=1
%endif

%install
%ifarch %{buildarches}
mkdir -p %{buildroot}/%{_datadir}/%{name}/
pushd src/bin/

cp -a undionly.kpxe ipxe.{iso,usb,dsk,lkrn} %{buildroot}/%{_datadir}/%{name}/

for fmt in %{formats};do
 for img in *.${fmt};do
      if [ -e $img ]; then
   cp -a $img %{buildroot}/%{_datadir}/%{name}/
   echo %{_datadir}/%{name}/$img >> ../../${fmt}.list
  fi
 done
done
popd

# the roms supported by qemu will be packaged separatedly
# remove from the main rom list and add them to qemu.list
for fmt in rom ;do
 for rom in %{qemuroms} ; do
  sed -i -e "/\/${rom}.${fmt}/d" ${fmt}.list
  echo %{_datadir}/%{name}/${rom}.${fmt} >> qemu.${fmt}.list
 done
done
%endif

%ifarch %{buildarches}
%files bootimgs
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/ipxe.iso
%{_datadir}/%{name}/ipxe.usb
%{_datadir}/%{name}/ipxe.dsk
%{_datadir}/%{name}/ipxe.lkrn
%{_datadir}/%{name}/undionly.kpxe
%doc COPYING COPYRIGHTS USAGE

%files roms -f rom.list
%dir %{_datadir}/%{name}
%doc COPYING COPYRIGHTS

%files roms-qemu -f qemu.rom.list
%dir %{_datadir}/%{name}
%doc COPYING COPYRIGHTS
%endif

