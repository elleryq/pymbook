# 安裝前言 #
本程式使用 python 與 pygtk 撰寫，理論上應可相容於各大主流 Linux distro。目前這裡只提供 Debian/Ubuntu 的 .deb 檔案，未來會再提供 .rpm 檔案，以利於 Fedora/RedHat/OpenSuSE/Mandrive 等 distro 來安裝。

# 支援的 Linux #

## Debian/Ubuntu ##
直接下載這裡提供的 .deb 檔案，使用 sudo dpkg -i <.deb> 安裝即可。

或者使用 PPA，先加入軟體來源：sudo add-apt-repository ppa:elleryq/ppa
加入完成後，先 sudo apt-get update
再用 sudo apt-get install pymbook 來安裝。

## 其他 ##
下載 .tar.gz 檔案並解開，執行 sudo ./setup.py install --record=install-files.txt ，即可安裝。

若需要反安裝，則到當初解開 .tar.gz 的目錄，執行 sudo ./setup.py uninstall --manifest=install-files.txt ，即可。