%define glib2_version 2.13.3
%define gtk2_version 2.10.0
%define desktop_file_utils_version 0.9
%define gnome_doc_utils_version 0.3.2
%define libgnome_version 2.13.7
%define libgnomeui_version 2.13.2
%define gnome_desktop_version 2.9.91
%define gnome_panel_version 2.9.4

Name:           gnome-utils
Version:        2.28.1
Release:        10%{?dist}
Epoch:          1

Summary:        GNOME utility programs

Group:          Applications/System
License:        GPLv2+
URL:            http://www.gnome.org
Source0:        http://download.gnome.org/sources/gnome-utils/2.28/gnome-utils-%{version}.tar.bz2

Patch0:         spinner.patch
Patch1:         0001-gsearchtool-Backport-the-version-fix.patch
# https://bugzilla.gnome.org/show_bug.cgi?id=597435
Patch2:         selfshot.patch

# make docs show up on rarian/yelp
Patch3:         gnome-utils-doc-category.patch

# updated translations
# https://bugzilla.redhat.com/show_bug.cgi?id=588738
Patch4:         gnome-utils-translations.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  gnome-doc-utils >= %{gnome_doc_utils_version}
BuildRequires:  glib2-devel >= %{glib2_version}
BuildRequires:  gtk2-devel >= %{gtk2_version}
BuildRequires:  gnome-desktop-devel >= %{gnome_desktop_version}
BuildRequires:  gnome-panel-devel >= %{gnome_panel_version}
BuildRequires:  libcanberra-devel
BuildRequires:  libXmu-devel
BuildRequires:  libX11-devel
BuildRequires:  libgtop2-devel
BuildRequires:  e2fsprogs-devel
BuildRequires:  usermode
BuildRequires:  gettext
BuildRequires:  intltool
BuildRequires:  gnome-common
BuildRequires:  automake autoconf libtool

Requires: gnome-utils-libs = %{epoch}:%{version}-%{release}

Requires(post): scrollkeeper
Requires(post): desktop-file-utils >= %{desktop_file_utils_version}
Requires(post): GConf2 >= 2.14
Requires(preun): GConf2 >= 2.14
Requires(pre): GConf2 >= 2.14

Requires(postun): scrollkeeper
Requires(postun): desktop-file-utils >= %{desktop_file_utils_version}

# obsolete the standalone baobab package from Extras
Obsoletes: baobab < %{version}-%{release}
Provides: baobab = %{version}-%{release}

%description
The gnome-utils package contains a set of small "desk accessory" utility
applications for GNOME, such as a dictionary, a disk usage analyzer,
a screenshot tool and others.

%package devel
Summary: Development files for gnome-utils
Group: Development/Libraries
Requires:  gnome-utils = %{epoch}:%{version}-%{release}
Requires: gnome-utils-libs = %{epoch}:%{version}-%{release}
Requires:  glib2-devel >= %{glib2_version}
Requires:  gtk2-devel >= %{gtk2_version}
Requires:  pkgconfig

%description devel
The gnome-utils-devel package contains header files and other resources
needed to develop programs using the libraries contained in gnome-utils.

%package libs
Summary: gnome-utils libraries
Group: Development/Libraries

%description libs
This package contains libraries provided by gnome-utils (such as libgdict)

%package -n gnome-system-log
Summary: A log file viewer for the GNOME desktop
Group: Applications/System
Requires: %{name} = %{epoch}:%{version}-%{release}
Requires: usermode

%description -n gnome-system-log
The gnome-system-log package contains an application that lets you
view various system log files.

%prep
%setup -q
%patch0 -p1 -b .spinner
%patch1 -p1 -b .version
%patch2 -p1 -b .selfshot
%patch3 -p1 -b .doc-category
%patch4 -p1 -b .translations

# Hide from menus
pushd gsearchtool
rm gnome-search-tool.desktop
rm gnome-search-tool.schemas
echo "NoDisplay=true" >> gnome-search-tool.desktop.in
popd

autoreconf -f -i

%build
%configure --disable-scrollkeeper --enable-console-helper
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT

export GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL=1
make install DESTDIR=$RPM_BUILD_ROOT
unset GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL

/bin/rm -rf $RPM_BUILD_ROOT%{_libdir}/*.a
/bin/rm -rf $RPM_BUILD_ROOT%{_libdir}/*.la

# make gnome-system-log use consolehelper until it starts using polkit
./mkinstalldirs $RPM_BUILD_ROOT%{_sysconfdir}/pam.d
/bin/cat <<EOF >$RPM_BUILD_ROOT%{_sysconfdir}/pam.d/gnome-system-log
#%%PAM-1.0
auth         include         config-util
account         include         config-util
session         include         config-util
EOF

./mkinstalldirs $RPM_BUILD_ROOT%{_sysconfdir}/security/console.apps
/bin/cat <<EOF >$RPM_BUILD_ROOT%{_sysconfdir}/security/console.apps/gnome-system-log
USER=root
PROGRAM=/usr/sbin/gnome-system-log
SESSION=true
FALLBACK=true
EOF

./mkinstalldirs $RPM_BUILD_ROOT%{_sbindir}
/bin/mv $RPM_BUILD_ROOT%{_bindir}/gnome-system-log $RPM_BUILD_ROOT%{_sbindir}
/bin/ln -s /usr/bin/consolehelper $RPM_BUILD_ROOT%{_bindir}/gnome-system-log


desktop-file-install --vendor gnome --delete-original       \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications             \
  $RPM_BUILD_ROOT%{_datadir}/applications/*

desktop-file-install --vendor gnome --delete-original       \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications             \
  --copy-generic-name-to-name             \
  $RPM_BUILD_ROOT%{_datadir}/applications/gnome-baobab.desktop

desktop-file-install --vendor gnome --delete-original       \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications             \
  --remove-category=Office              \
  --add-category=Utility             \
  $RPM_BUILD_ROOT%{_datadir}/applications/gnome-dictionary.desktop

# save space by linking identical images in translated docs
for n in baobab gnome-dictionary gnome-search-tool gnome-system-log; do
  helpdir=$RPM_BUILD_ROOT%{_datadir}/gnome/help/$n
  for f in $helpdir/C/figures/*.png; do
    for d in $helpdir/*; do
      if [ -d "$d" -a "$d" != "$helpdir/C" ]; then
        g="$d/figures/$b"
        if [ -f "$g" ]; then
          if cmp -s $f $g; then
            rm "$g"; ln -s "../../C/figures/$b" "$g"
          fi
        fi
      fi
    done
  done
done

%find_lang gnome-utils-2.0
%find_lang baobab --with-gnome
%find_lang gnome-dictionary --with-gnome
%find_lang gnome-search-tool --with-gnome
%find_lang gnome-system-log --with-gnome

cat baobab.lang >> gnome-utils-2.0.lang
cat gnome-dictionary.lang >> gnome-utils-2.0.lang
cat gnome-search-tool.lang >> gnome-utils-2.0.lang

%clean
rm -rf $RPM_BUILD_ROOT


%post
/sbin/ldconfig
scrollkeeper-update -q
update-desktop-database -q
export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
gconftool-2 --makefile-install-rule \
         %{_sysconfdir}/gconf/schemas/gnome-dictionary.schemas \
         %{_sysconfdir}/gconf/schemas/gnome-search-tool.schemas \
         %{_sysconfdir}/gconf/schemas/gnome-screenshot.schemas \
         %{_sysconfdir}/gconf/schemas/baobab.schemas \
         >& /dev/null || :
touch --no-create %{_datadir}/icons/hicolor
if [ -x /usr/bin/gtk-update-icon-cache ]; then
  gtk-update-icon-cache -q %{_datadir}/icons/hicolor
fi

%pre
if [ "$1" -gt 1 ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  for f in gnome-dictionary.schemas logview.schemas gnome-system-log.schemas gnome-search-tool.schemas gnome-screenshot.schemas baobab.schemas; do
    if [ -f %{_sysconfdir}/gconf/schemas/$f ]; then
      gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/$f >& /dev/null || :
    fi
  done
fi

%preun
if [ "$1" -eq 0 ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  for f in gnome-dictionary.schemas logview.schemas gnome-system-log.schemas gnome-search-tool.schemas gnome-screenshot.schemas baobab.schemas; do
    if [ -f %{_sysconfdir}/gconf/schemas/$f ]; then
      gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/$f >& /dev/null || :
    fi
  done
fi

%postun
/sbin/ldconfig
scrollkeeper-update -q
update-desktop-database -q
touch --no-create %{_datadir}/icons/hicolor
if [ -x /usr/bin/gtk-update-icon-cache ]; then
  gtk-update-icon-cache -q %{_datadir}/icons/hicolor
fi


%post -n gnome-system-log
scrollkeeper-update -q
export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
gconftool-2 --makefile-install-rule \
         %{_sysconfdir}/gconf/schemas/gnome-system-log.schemas \
         >& /dev/null || :

%pre -n gnome-system-log
if [ "$1" -gt 1 ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/gnome-system-log.schemas >& /dev/null || :
fi

%preun -n gnome-system-log
if [ "$1" -eq 0 ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/gnome-system-log.schemas >& /dev/null || :
fi


%files -f gnome-utils-2.0.lang
%defattr(-,root,root,-)
%doc COPYING NEWS README
%doc gnome-dictionary/AUTHORS
%doc gnome-dictionary/README
%doc gsearchtool/AUTHORS
%doc baobab/AUTHORS
%doc baobab/README
%{_sysconfdir}/gconf/schemas/gnome-dictionary.schemas
%{_sysconfdir}/gconf/schemas/gnome-screenshot.schemas
%{_sysconfdir}/gconf/schemas/gnome-search-tool.schemas
%{_sysconfdir}/gconf/schemas/baobab.schemas
%{_bindir}/gnome-dictionary
%{_bindir}/gnome-panel-screenshot
%{_bindir}/gnome-screenshot
%{_bindir}/gnome-search-tool
%{_bindir}/baobab
%{_datadir}/applications/gnome-dictionary.desktop
%{_datadir}/applications/gnome-screenshot.desktop
%{_datadir}/applications/gnome-search-tool.desktop
%{_datadir}/applications/gnome-baobab.desktop
%{_datadir}/gdict-1.0/
%{_datadir}/gnome-dictionary/
%{_datadir}/gnome-screenshot/
%{_datadir}/baobab/
%{_datadir}/pixmaps/gsearchtool/
%{_datadir}/icons/hicolor/24x24/apps/baobab.png
%{_datadir}/icons/hicolor/scalable/apps/baobab.svg
%{_libexecdir}/gnome-dictionary-applet
%{_datadir}/gnome-2.0/ui/GNOME_DictionaryApplet.xml
%{_libdir}/bonobo/servers/GNOME_DictionaryApplet.server
%{_mandir}/man1/gnome-dictionary.1.gz
%{_mandir}/man1/gnome-search-tool.1.gz
%{_mandir}/man1/baobab.1.gz
%{_mandir}/man1/gnome-screenshot.1.gz

%files devel
%defattr(-,root,root,-)
%{_libdir}/libgdict-1.0.so
%{_libdir}/pkgconfig/gdict-1.0.pc
%{_includedir}/gdict-1.0/
%{_datadir}/gtk-doc/html/gdict/

%files libs
%defattr(-, root, root)
%{_libdir}/libgdict-1.0.so.*

%files -n gnome-system-log -f gnome-system-log.lang
%defattr(-,root,root,-)
%{_bindir}/gnome-system-log
%{_sbindir}/gnome-system-log
%{_datadir}/gnome-utils/
%{_sysconfdir}/gconf/schemas/gnome-system-log.schemas
%{_sysconfdir}/security/console.apps/gnome-system-log
%{_sysconfdir}/pam.d/gnome-system-log
%{_datadir}/applications/gnome-system-log.desktop
%{_mandir}/man1/gnome-system-log.1.gz

%changelog
* Fri Aug 06 2010 Ray Strode <rstrode@redhat.com> 2.28.1-10
- Update translations
  Resolves: #575699

* Fri Jul 02 2010 Ray Strode <rstrode@redhat.com> 2.28.1-9
- rebuild
  Resolves: #609758

* Wed May 26 2010 Matthias Clasen <mclasen@redhat.com> 2.28.0-8
- Add explicit requires to avoid interoperability problems
  between combinations of old and new subpackages
- Remove a space-saving hack that causes multilib conflicts
Resolves: #596165

* Tue May 11 2010 Matthias Clasen <mclasen@redhat.com> 2.28.0-7
- Updated translations
Resolves: #588738

* Mon May  3 2010 Matthias Clasen <mclasen@redhat.com> 2.28.0-6
- Make docs show up in yelp
Resolves: #588567

* Thu Jan 28 2010 Ray Strode <rstrode@redhat.com> 2.28.0-5
Resolves: #559776
- spec clean ups

* Tue Nov 24 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.28.1-4
- Avoid segfault with gnome-screenshot self-portraits (#541006)

* Sun Oct 25 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.28.1-3
- Fix the --version command (#516491)

* Fri Oct 23 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.28.1-2
- Fix the gsearchtool spinner

* Fri Oct 23 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.28.1-1
- Update to 2.28.1

* Mon Oct  5 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.28.0-2
- Move the usermode dep to the gnome-system-log package (#527295)

* Mon Sep 21 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.28.0-1
- Update to 2.28.0

* Thu Sep 17 2009 Ray Strode <rstrode@redhat.com> - 1:2.27.91-2
- Split off -libs package

* Mon Aug 24 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.27.91-1
- Update to 2.27.91

* Sat Aug 22 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.27.2-6
- Fix a crash in gnome-dictionary

* Fri Jul 31 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.27.2-5
- Fix a typo

* Thu Jul 30 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.27.2-4
- Split off a gnome-system-log subpackage
- Move gnome-dictionary to a better place in the menus

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:2.27.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul  2 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.27.2-2
- Shrink some more schemas

* Tue Jun 16 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.27.2-1
- Update to 2.27.2

* Mon May 15 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.27.1-1
- Update to 2.27.1

* Mon Apr 27 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.26.0-2
- Don't drop schemas translations from po files

* Mon Mar 16 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.26.0-1
- Update to 2.26.0

* Mon Mar  2 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.25.92-1
- Update to 2.25.92

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:2.25.90-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Sat Feb 21 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.25.90-4
- Don't include nonexisting logfiles in the default list

* Sat Feb 14 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.25.90-3
- Install the right gconf schemas

* Tue Feb  3 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.25.90-2
- Update to 2.25.90

* Sun Jan 11 2009 Matthias Clasen <mclasen@redhat.com> - 1:2.25.2-1
- Update to 2.25.2

* Mon Dec 22 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.25.0-3
- Update to 2.25.0

* Wed Dec 17 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.24.1-4
- Rebuild against new gnome-desktop

* Sun Nov 23 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.24.1-3
- Improve description

* Thu Nov 13 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.24.1-2
- Rebuild

* Mon Oct 20 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.24.1-1
- Update to 2.24.1

* Fri Oct 10 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.24.0-3
- Save space

* Mon Sep 22 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.24.0-1
- Update to 2.24.0

* Mon Sep  8 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.23.92-1
- Update to 2.23.92

* Thu Aug 28 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.23.90-2
- Fix a crash in gnome-screenshot

* Tue Aug 26 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.23.90-1
- Update to 2.23.90
- Drop upstreamed patches

* Thu Jul 24 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.20.0.0.1-8
- Use standard icon names

* Wed Jun  4 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.20.0.0.1-7
- Rebuild

* Thu May 22 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.20.0.0.1-6
- Fix a directory ownership bug

* Wed Apr 23 2008 Matthias Clasen <mclasen@redhat.com> - 1:2.20.0.0.1-5
- Fix ugly display of URIs in screenshot replace dialog (#443769)

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 1:2.20.0.1-4
- Autorebuild for GCC 4.3

* Fri Nov 16 2007 Matthias Clasen <mclasen@redhat.com> - 2.20.0.1-3
- Don't crash when multiple versions are present (#386511)
- Make gnome-system-log pick up the versioning of rsyslog

* Thu Oct 18 2007 Matthias Clasen <mclasen@redhat.com> - 2.20.0.1-2
- Fix some crashes when scrolling (#321701)

* Tue Sep 18 2007 Matthias Clasen <mclasen@redhat.com> - 2.20.0.1-1
- Update to 2.20.0.1

* Mon Sep 17 2007 Matthias Clasen <mclasen@redhat.com> - 2.20.0-1
- Update to 2.20.0

* Thu Sep  6 2007 Matthias Clasen <mclasen@redhat.com> - 2.19.92-1
- Update to 2.19.92

* Tue Sep  4 2007 Matthias Clasen <mclasen@redhat.com> - 2.19.91-1
- Update to 2.19.91

* Thu Aug 23 2007 Adam Jackson <ajax@redhat.com> - 1:2.19.90-2
- Rebuild for build ID

* Mon Aug 13 2007 Matthias Clasen <mclasen@redhat.com> - 2.19.90-1
- Update to 2.19.90

* Tue Aug  7 2007 Matthias Clasen <mclasen@redhat.com> - 2.18.1-3
- Update license field
- Use %%find_lang for help files
- Update file lists

* Fri Jul  6 2007 Matthias Clasen <mclasen@redhat.com> - 2.18.1-2
- Fix tempdir handling in gnome-screenshot (#246687)

* Sun May 20 2007 Matthias Clasen <mclasen@redhat.com> - 2.18.1-1
- Update to 2.18.1

* Tue Mar 13 2007 Matthias Clasen <mclasen@redhat.com> - 2.18.0-1
- Update to 2.18.0

* Tue Feb 13 2007 Matthias Clasen <mclasen@redhat.com> - 2.17.92-1
- Update to 2.17.92

* Wed Jan 24 2007 Matthias Clasen <mclasen@redhat.com> - 2.17.91-1
- Update to 2.17.91

* Mon Jan 22 2007 Matthias Clasen <mclasen@redhat.com> - 2.17.90-1
- Update to 2.17.90
- Drop requires for gcalctool, gucharmap, zenity

* Wed Jan 10 2007 Matthias Clasen <mclasen@redhat.com> - 2.17.1-1
- Update to 2.17.1

* Mon Nov  6 2006 Matthias Clasen <mclasen@redhat.com> - 2.17.0-1
- Update to 2.17.0
- Temporarily build without api docs and baobab icon

* Fri Nov  3 2006 Matthias Clasen <mclasen@redhat.com> - 2.16.1-2
- Silence %%pre

* Sat Oct 21 2006 Matthias Clasen <mclasen@redhat.com> - 2.16.1-1
- Update to 2.16.1

* Wed Oct 18 2006 Matthias Clasen <mclasen@redhat.com> - 2.16.0-2
- Fix scripts according to the packaging guidelines

* Mon Sep  4 2006 Matthias Clasen <mclasen@redhat.com> - 2.16.0-1.fc6
- Update to 2.16.0

* Fri Aug 25 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.94-1.fc6
- Update to 2.15.94

* Mon Aug 21 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.93-1.fc6
- Update to 2.15.93
- Require pkgconfig in the devel package

* Sat Aug 12 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.92-1.fc6
- Update to 2.15.92

* Thu Aug  3 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.90-1.fc6
- Update to 2.15.90

* Tue Jul 25 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.3-2
- Obsolete the baobab package from Extras (#191298)

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 2.15.3-1.1
- rebuild

* Tue Jun 13 2006 Matthias Clasen <mclasen@redhat.com> 2.15.3-1
- Update to 2.15.3

* Sat Jun 10 2006 Matthias Clasen <mclasen@redhat.com> 2.15.0-3
- More missing BuildRequires
- Use --enable-console-helper 

* Sun May 21 2006 Matthias Clasen <mclasen@redhat.com> 2.15.0-2
- Add missing BuildRequires (#129097)

* Tue May  9 2006 Matthias Clasen <mclasen@redhat.com> 2.15.0-1
- Update to 2.15.0

* Wed Apr 19 2006 Jeremy Katz <katzj@redhat.com> - 1:2.14.0-10
- fix -devel requires on main package

* Wed Apr 19 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-9
- Fix some crashes in gdict (#189090)

* Tue Apr 18 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-8
- Re-add the epoch

* Tue Apr 18 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-7
- Bump rev

* Tue Apr 18 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-6
- Incorporate package review feedback
- Split off a -devel subpackage
 
* Tue Apr 11 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-5
- Split off gucharmap, zenity, gcalctool

* Mon Mar 13 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-3
- Update to zenity 2.14.0

* Mon Mar 13 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-2
- Update to gcalctool 5.7.32

* Mon Mar 13 2006 Matthias Clasen <mclasen@redhat.com> 2.14.0-1
- Update to gnome-utils 2.14.0
- Update to gucharmap 1.6.0

* Sat Mar  4 2006 Matthias Clasen <mclasen@redhat.com> 2.13.95-1
- Update to gnome-utils-2.13.95

* Wed Mar 01 2006 Karsten Hopp <karsten@redhat.de> 2.13.93-2
- BuildRequires:  gnome-doc-utils

* Sat Feb 25 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.93-1
- Update to gnome-utils-2.13.93
- Update to gucharmap 1.5.3

* Mon Feb 20 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.92-4
- Fix a crash in gnome-system-log when closing logs

* Wed Feb 15 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.92-3
- Fix %%post 

* Wed Feb 15 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.92-2
- Update to gucharmap 1.5.2
- Update to gcalctool 5.7.29

* Sun Feb 12 2006 Matthias Clasen <mclasen@redhat.com> 2.13.92-1
- Update to gnome-utils 2.13.92

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 1:2.13.91-2.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 1:2.13.91-2.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Mon Feb  6 2006 Matthias Clasen <mclasen@redhat.com> 2.13.91-2
- Fix a gnome-system-log crash

* Mon Jan 30 2006 Matthias Clasen <mclasen@redhat.com> 2.13.91-1
- Update to gnome-utils 2.13.91
- Update to zenity 2.13.90
- Update to gucharmap 1.5.1
- Update to gcalctool 5.7.28

* Mon Jan 23 2006 Ray Strode <rstrode@redhat.com> 2.13.5-4
- Update to gcalctool 5.7.27

* Sun Jan 22 2006 Ray Strode <rstrode@redhat.com> 2.13.5-3
- Update to gcalctools 5.7.26
- fix subtract operator

* Tue Jan 17 2006 Matthias Clasen <mclasen@redhat.com> 2.13.5-2
- gdict.schemas got renamed

* Mon Jan 16 2006 Matthias Clasen <mclasen@redhat.com> 2.13.5
- Update to gnome-utils 2.13.5
- Update to zenity 2.13.5

* Tue Jan 03 2006 Matthias Clasen <mclasen@redhat.com> 2.13.4
- Update to gnome-utils 2.13.4
- Update to gcalctool 5.7.18

* Thu Dec 15 2005 Matthias Clasen <mclasen@redhat.com> 2.13.3
- Update to gnome-utils 2.13.3
- Update to zenity 2.13.3
- Update to gucharmap 1.5.0
- Update to gcalctool 5.7.15
- Drop upstreamed patch

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com> 
- rebuilt

* Thu Dec 01 2005 John (J5) Palmieri <johnp@redhat.com>
- rebuild for new dbus

* Wed Nov 30 2005 Matthias Clasen <mclasen@redhat.com>
- Update to gnome-utils 2.13.2, zenity 2.13.2 and
  gcalctool 5.7.11

* Tue Nov 22 2005 Matthias Clasen <mclasen@redhat.com>
- classify gnome-system-log as Monitor for better menus

* Thu Nov 3 2005 Ray Strode <rstrode@redhat.com> - 1:2.13.1-2
- remove unnecessary Requires (bug 172365)
- use make install DESTDIR instead of %%makeinstall

* Tue Nov 1 2005 Ray Strode <rstrode@redhat.com> - 1:2.13.1-1
- update to gnome-utils 2.13.1

* Thu Oct 13 2005 Tomas Mraz <tmraz@redhat.com>
- use include config-util instead of pam_stack in pam config

* Thu Oct 13 2005 Matthias Clasen <mclasen@redhat.com> - 1:2.12.1-3
- Add missing Requires

* Wed Oct 12 2005 Matthias Clasen <mclasen@redhat.com> - 1:2.12.1-2
- No need to call update-gtk-immodules in %%post, since gucharmap
  does not include the input method anymore

* Thu Oct  6 2005 Matthias Clasen <mclasen@redhat.com> - 1:2.12.1-1
- Update to gnome-utils 2.12.1 and zenity 2.12.1

* Thu Sep 29 2005 Matthias Clasen <mclasen@redhat.com> - 1:2.12.0-2
- Make gnome-system-log use consolehelper (#169535)

* Thu Sep  8 2005 Matthias Clasen <mclasen@redhat.com> - 1:2.12.0-1
- Update to gnome-utils 2.12.0, gcalctool 5.6.31, zenity 2.12.0,
  gucharmap 1.4.4

* Tue Aug 16 2005 Warren Togami <wtogami@redhat.com> - 1:2.11.91-3
- rebuild for new cairo

* Sat Aug 13 2005 Ray Strode <rstrode@redhat.com> 1:2.11.91-2
- Reenable log viewer (bug 163260)
- add buildreqs for flex/bison

* Tue Aug  9 2005 Ray Strode <rstrode@redhat.com> 1:2.11.91-1
- Update to gnome-utils 2.11.91, gcalctool 5.6.26, zenity 2.11.90

* Fri Aug  5 2005 Matthias Clasen <mclasen@redhat.com> 1:2.11.90-1
- Update to gnome-utils 2.11.90, gcalctool 5.6.25, zenity 2.11.90

* Fri Jul  8 2005 Matthias Clasen <mclasen@redhat.com> 1:2.11.1-1
- Update to gnome-utils 2.11.1, gcalctool 5.6.14, zenity 2.11.0

* Tue May 17 2005 Ray Strode <rstrode@redhat.com> 1:2.10.0-3
- call more autofoo to allow recompilation on x86_64 (bug 150627) 

* Sun Apr 24 2005 Ray Strode <rstrode@redhat.com> 1:2.10.0-2
- install gnome-screenshot schema (bug 155809)

* Sun Apr  3 2005 Ray Strode <rstrode@redhat.com> 1:2.10.0-1
- update to gnome-utils 2.10.0, zenity 2.10.0, gcalctool 5.5.41

* Tue Mar  8 2005 John (J5) Palmieri <johnp@redhat.com> 1:2.9.92-3
- Fixed up gfloppy for new HAL 0.5.0 api

* Thu Mar  3 2005 Marco Pesenti Gritti <mpg@redhat.com> 1:2.9.92-2
- Rebuild

* Mon Feb 28 2005 Matthias Clasen <mclasen@redhat.com> 1:2.9.92-1
- Update to gnome-utils, zenity 2.9.92

* Wed Feb  9 2005 Matthias Clasen <mclasen@redhat.com> 1:2.9.91-1
- Update to gnome-utils 2.9.91, zenity 2.9.91, gcalctool 5.5.34

* Thu Jan 27 2005 Matthias Clasen <mclasen@redhat.com> 1:2.9.90-1 
- Update to gnome-utils 2.9.90,
  zenity 2.9.2 and gcalctool 5.5.29
- Drop obsolete patches

* Sat Nov  6 2004 Marco Pesenti Gritti <mpg@redhat.com> 1:2.8.1-1
- Update to gnome-utils 2.8.1
- Update to zenity 2.8.1
- Update to gucharmap 1.4.2

* Thu Nov  4 2004 Marco Pesenti Gritti <mpg@redhat.com> 1:2.8.0-7
- Use _host to locate update-gtk-immodule as gtk does. Fix #124484

* Wed Oct 20 2004 Miloslav Trmac <mitr@redhat.com> - 1:2.8.0-6
- Run ldconfig in %%post and %%postun

* Mon Oct 18 2004 Marco Pesenti Gritti <mpg@redhat.com> 1:2.8.0-5
- #136032 Downgrade gucharmap to 4.8.20 (stable series). 5.x
  was used by mistake.

* Thu Sep 30 2004 Christopher Aillon <caillon@redhat.com> 1:2.8.0-4
- PreReq desktop-file-utils >= 0.9
- update-desktop-database on uninstall

* Tue Sep 28 2004 Ray Strode <rstrode@redhat.com> 1:2.8.0-3
- Hide Search Tool from menus using spec file foo instead of patch file

* Tue Sep 28 2004 Ray Strode <rstrode@redhat.com> 1:2.8.0-2
- Hide Search Tool from menus
- Require recent version of desktop-file-utils since update-desktop-database
  is called.

* Wed Sep 22 2004 Christopher Aillon <caillon@redhat.com> 1:2.8.0-1
- Update to 2.8.0 and zenity 2.8.0

* Tue Aug 31 2004 Alex Larsson <alexl@redhat.com> 1:2.7.91-1
- update to 2.7.91 and zenity 2.7.91

* Thu Aug 19 2004 Christopher Aillon <caillon@redhat.com> 1.2.7.90-1
- Update to gnome-utils 2.7.90
- Update to zenity 2.7.90
- Update to gcalctool 5.5.0
- Call update-desktop-database for gfloppy

* Wed Jun 30 2004 Christopher Aillon <caillon@redhat.com> 1:2.6.2-1
- Update to gnome-utils 2.6.2
- Update to zenity 2.6.2
- Update to gcalctool 4.4.8

* Mon Jun 28 2004 Dan Williams <dcbw@redhat.com>
- Update to the new mechanism of updating arch-dependent gtk config files.
- Update to gnome-utils 2.6.1

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Wed Apr 14 2004 Warren Togami <wtogami@redhat.com> 1:2.6.0-2
- #111124 BR gnome-desktop-devel gettext

* Fri Apr  2 2004 Alex Larsson <alexl@redhat.com> 1:2.6.0-1
- update to the 2.6 releases

* Wed Mar 10 2004 Alex Larsson <alexl@redhat.com> 1:2.5.90-1
- update to latest versions

* Tue Mar 02 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Thu Feb 26 2004 Alexander Larsson <alexl@redhat.com> 1:2.5.2-3
- update zenity, gcalctool, gucharmap

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Fri Jan 30 2004 Alexander Larsson <alexl@redhat.com> 1:2.5.2-1
- update to latest

* Thu Sep 11 2003 Alexander Larsson <alexl@redhat.com> 1:2.4.0-1
- Update to the final 2.4.0 release

* Fri Aug 22 2003 Alexander Larsson <alexl@redhat.com> 1:2.3.4-2
- use configure option instead of patch

* Wed Aug 20 2003 Alexander Larsson <alexl@redhat.com> 1:2.3.4-1
- update for gnome 2.3, import zenity, gucharmap & gcalctool

* Tue Jul 29 2003 Havoc Pennington <hp@redhat.com> 1:2.2.3-2
- rebuild

* Mon Jul  7 2003 Havoc Pennington <hp@redhat.com> 1:2.2.3-1
- 2.2.3

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Fri Feb 14 2003 Havoc Pennington <hp@redhat.com> 1:2.2.0.3-2
- remove Xft buildreq

* Wed Feb  5 2003 Havoc Pennington <hp@redhat.com> 1:2.2.0.3-1
- 2.2.0.3

* Sun Feb 02 2003 Florian La Roche <Florian.LaRoche@redhat.de>
- builds again on s390x

* Fri Jan 24 2003 Jonathan Blandford <jrb@redhat.com>
- install all the schemas files
- new version; ExcludeArch: s390x
 
* Wed Jan 22 2003 Tim Powers <timp@redhat.com>
- rebuilt

* Wed Dec 18 2002 Elliot Lee <sopwith@redhat.com> 2.1.4-2
- Add alphabitops.patch so it builds on the alpha (asm/bitops.h of which 
has 'extern' instead of 'static')

* Fri Dec 13 2002 Tim Powers <timp@redhat.com> 1:2.1.4-1
- update to 2.1.4

* Tue Sep  3 2002 Matt Wilson <msw@redhat.com>
- corrected the return code 3 gdialog dialog types

* Wed Aug 28 2002 Tim Waugh <twaugh@redhat.com>
- Fix gnome-calculator key bindings (bug #67885).

* Thu Aug 15 2002 Havoc Pennington <hp@redhat.com>
- enable gdialog by popular demand
- build require e2fsprogs-devel so gfloppy builds
- patch for #70258 (locate doesn't notice new files)

* Mon Aug 12 2002 Havoc Pennington <hp@redhat.com>
- 2.0.2

* Thu Aug  1 2002 Havoc Pennington <hp@redhat.com>
- build require newer versions of things
- 2.0.1
- remove gnome-system-log and more thoroughly remove archive-generator

* Tue Jul 23 2002 Havoc Pennington <hp@redhat.com>
- remove archive-generator, duplicates file-roller

* Wed Jun 26 2002 Owen Taylor <otaylor@redhat.com>
- Fix find_lang

* Wed Jun 19 2002 Havoc Pennington <hp@redhat.com>
- disable schema install in make install, fixes rebuild

* Mon Jun 17 2002 Havoc Pennington <hp@redhat.com>
- 2.0.0
- use desktop-file-install

* Tue May 28 2002 Havoc Pennington <hp@redhat.com>
- rebuild in different environment

* Tue May 28 2002 Havoc Pennington <hp@redhat.com>
- move to GNOME 2 version

* Mon Apr 15 2002 Havoc Pennington <hp@redhat.com>
- merge translations

* Tue Mar  5 2002 Havoc Pennington <hp@redhat.com>
- put gdialog back since the nautilus scripts fad has everyone asking for it,
  #54415
- depend on automake-1.4 binary instead of automake14
- strip trailing newline from data in guname, #52598
- build requires libglade-devel

* Tue Feb  5 2002 Bill Nottingham <notting@redhat.com>
- get rid of weird binary names

* Wed Jan 30 2002 Jonathan Blandford <jrb@redhat.com>
- Rebuild package.

* Mon Jan 21 2002 Havoc Pennington <hp@redhat.com>
- automake14
- /usr/foo to bindir etc.
- use makeinstall and configure macros
- patch for glade header move

* Mon Aug 27 2001 Havoc Pennington <hp@redhat.com>
- Add po files from sources.redhat.com

* Sun Jun 24 2001 Elliot Lee <sopwith@redhat.com>
- Bump release + rebuild.

* Thu Apr 19 2001 Jonathan Blandford <jrb@redhat.com>
- new version

* Thu Mar 15 2001 Havoc Pennington <hp@redhat.com>
- translations

* Fri Feb 23 2001 Trond Eivind Glomsrød <teg@redhat.com>
- use %%{_tmppath}
- move changelog to end of file
- langify, remember to run %%find_lang twice as there
  are two different sets of locale files

* Thu Feb 08 2001 Owen Taylor <otaylor@redhat.com>
- Fix missing gfloppy.keys, gfloppy.mime files

* Mon Jan 29 2001 Havoc Pennington <hp@redhat.com>
- add dialog-prefs.glade file which was missing from upstream tarball; 
  fixes #25036

* Fri Jan 19 2001 Havoc Pennington <hp@redhat.com>
- 1.2.1
- remove patch for gdict segfault, fixed upstream
- remove logview, cromagnon, gdiskfree, gstripchart, 
  splash, gdialog, gw, idetool
- run automake so removals take effect

* Mon Aug 21 2000 Havoc Pennington <hp@redhat.com>
- patch from Tim Waugh to fix segfault on cancel in the settings
  dialog; bug 16477
- put in an error dialog if no DNS, bug 16475

* Mon Aug 21 2000 Havoc Pennington <hp@redhat.com>
- Put gcolorsel glade files in the file list, closes
  14314

* Fri Aug 11 2000 Jonathan Blandford <jrb@redhat.com>
- Up Epoch and release

* Sat Aug 05 2000 Havoc Pennington <hp@redhat.com>
- Use mail not mailx in guname, bug 14316

* Mon Jul 17 2000 Havoc Pennington <hp@redhat.com>
- remove Docdir

* Thu Jul 13 2000 Prospector <bugzilla@redhat.com>
- automatic rebuild

* Mon Jun 19 2000 Elliot Lee <sopwith@redhat.com>
- 1.2.0

* Fri May 19 2000 Havoc Pennington <hp@redhat.com>
- Add gfloppy .glade file to file list

* Fri May 19 2000 Havoc Pennington <hp@redhat.com>
- 1.1.0; remove man pages glob from file list (upstream no 
  longer comes with man pages)

* Thu May 11 2000 Matt Wilson <msw@redhat.com>
- 1.0.51

* Mon Feb 14 2000 Elliot Lee <sopwith@redhat.com>
- Add -mieee to CFLAGS to fix bug #9346.

* Fri Feb 04 2000 Owen Taylor <otaylor@redhat.com>
- minor patch to fix up size requisition in guname

* Thu Feb 03 2000 Preston Brown <pbrown@redhat.com>
- rebuild to pick up gzipped man page

* Thu Feb 3 2000 Jonathan Blandford <jrb@redhat.com>
- added patch to allow negative time to gtt.

* Sun Aug 1 1999 Dax Kelson <dax@gurulabs.com>
- version 1.0.12

* Fri Mar 19 1999 Michael Fulbright <drmike@redhat.com>
- strip binaries

* Sun Mar 14 1999 Michael Fulbright <drmike@redhat.com>
- removed gshutdown (confusing for newbies)

* Mon Feb 15 1999 Michael Fulbright <drmike@redhat.com>
- version 0.99.8

* Sat Feb 06 1999 Michael Fulbright <drmike@redhat.com>
- version 0.99.6

* Mon Jan 18 1999 Michael Fulbright <drmike@redhat.com>
- version 0.99.3

* Wed Jan 06 1999 Michael Fulbright <drmike@redhat.com>
- version 0.99.1

* Wed Dec 16 1998 Michael Fulbright <drmike@redhat.com>
- updated for GNOME freeze

* Wed Sep 23 1998 Michael Fulbright <msf@redhat.com>
- Upgraded to 0.30

* Mon Apr  6 1998 Marc Ewing <marc@redhat.com>
- Integrate into gnome-utils CVS source tree
