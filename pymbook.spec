Name:           pymbook
Version:        0.4
Release:        0%{?dist}
Summary:        A reader application for http://www.haodoo.net

Group:          Utilities/Desktops
License:        GPL-3.0-or-later
URL:            http://code.google.com/p/pymbook
Source0:        pymbook-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python3-devel python3-setuptools gettext intltool desktop-file-utils
Requires:       python3 python3-gobject gtk3 python3-cairo desktop-file-utils

%description
A reader application for http://www.haodoo.net .  This is a project for
reading haodoo .pdb files.

%prep
%setup -q
%build
%{python3} setup.py build


%install
rm -rf %{buildroot}
%{python3} setup.py install --skip-build --root %{buildroot} --prefix=%{_prefix}
%find_lang %{name}
rm -f %{buildroot}/%{_datadir}/icons/hicolor/icon-theme.cache


%clean
rm -rf %{buildroot}


%files -f %{name}.lang
%defattr(-,root,root)
%doc COPYING
%{_bindir}/%{name}
%{python3_sitelib}/*
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
