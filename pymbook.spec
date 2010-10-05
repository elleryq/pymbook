%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           pymbook
Version:        0.4
Release:        0%{?dist}
Summary:        A reader application for http://www.haodoo.net

Group:          Utilities/Desktops
License:        GPLv3
URL:            http://code.google.com/p/pymbook
Source0:        pymbook-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel gettext desktop-file-utils
Requires:       gtk2 desktop-file-utils

%description
A reader application for http://www.haodoo.net .  This is a project for
reading haodoo .pdb files.

%prep
%setup -q
sed -i '/#! \?\/usr.*/d' pymbooklib/*.py


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
%find_lang %{name}
rm -f %{buildroot}/%{_datadir}/icons/hicolor/icon-theme.cache
rm -f %{buildroot}/%{_datadir}/applications/%{name}.desktop
desktop-file-install --dir=${RPM_BUILD_ROOT}%{_datadir}/applications data/%{name}.desktop --vendor=""


%clean
rm -rf %{buildroot}


%files -f %{name}.lang
%defattr(-,root,root)
%doc COPYING
%{_bindir}/%{name}
%{python_sitelib}/*
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/*/%{name}*.png
%{_datadir}/icons/hicolor/*/*/%{name}*.svg
%{_datadir}/pixmaps/%{name}.png


%post
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor &>/dev/null || :


%postun
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor &>/dev/null || :


%changelog
* Tue Oct 5 2010 Yan-ren Tsai <elleryq@gmail.com> 0.4-0
- Initial release for Fedora.
    Note that this specfile is tested.
