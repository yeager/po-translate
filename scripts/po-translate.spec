Name:           po-translate
Version:        1.5.0
Release:        1%{?dist}
Summary:        Batch translate PO and TS localization files
License:        GPL-3.0-or-later
URL:            https://github.com/yeager/po-translate
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.10
Requires:       python3-polib

%description
A CLI tool for batch translating PO and TS files using
various translation APIs (Google, DeepL, Claude, etc.).

%prep
%setup -q

%install
mkdir -p %{buildroot}/usr/bin
install -m 755 po_translate.py %{buildroot}/usr/bin/po-translate

mkdir -p %{buildroot}/usr/share/man/man1
install -m 644 man/po-translate.1.gz %{buildroot}/usr/share/man/man1/

mkdir -p %{buildroot}/usr/share/doc/%{name}
install -m 644 README.md CHANGELOG.md %{buildroot}/usr/share/doc/%{name}/

%post
# Nothing needed for CLI-only tool

%postun
# Nothing needed for CLI-only tool

%files
/usr/bin/po-translate
/usr/share/man/man1/po-translate.1.gz
%doc /usr/share/doc/%{name}/README.md
%doc /usr/share/doc/%{name}/CHANGELOG.md
%license LICENSE

%changelog
* Mon Feb 09 2026 Daniel Nylander <daniel@danielnylander.se> - 1.4.0-1
- Updated translation engine support
- Bug fixes and improvements
