# pymbook

pymbook 是一個以 GTK 桌面環境執行的電子書閱讀器，主要用來閱讀 [Haodoo](https://www.haodoo.net) 提供的 PDB/uPDB 書籍檔案。程式讀取本機檔案；不會連線至 Haodoo 搜尋或下載書籍。

## 支援格式

- `.pdb`：Haodoo 傳統文字格式，使用 CP950 編碼。
- `.updb`：Haodoo Unicode 格式。

目前不支援 EPUB、PDF 或其他電子書格式。書籍檔案不包含在此原始碼中。

## 執行需求

這是以 Python 2 和 GTK 2/PyGTK 2 撰寫的舊版應用程式，尚未支援 Python 3。執行前需安裝：

- Python 2.5 或更新版本（原專案建議 Python 2.6）
- GTK 2 與 PyGTK 2
- GTK 繪圖所需的 Pango、Cairo 元件

若要建置翻譯及桌面項目，另需 `msgfmt`（gettext）和 `intltool-merge`。

## 安裝與啟動

若作業系統仍提供 pymbook 套件，建議使用系統的套件管理器安裝。也可在已安裝上述相依套件的環境中，從原始碼目錄直接啟動：

```sh
./pymbook
```

啟動時開啟指定書籍：

```sh
./pymbook /path/to/book.pdb
```

也可使用 `python2 ./pymbook /path/to/book.updb` 開啟 uPDB。未指定檔案時，可透過「開啟」對話框選擇書籍，或從書架載入書籍。

以原始碼安裝（需具備相依套件與建置工具）：

```sh
python2 setup.py build
python2 setup.py install --record=install-files.txt
```

`INSTALL` 檔案提供其他安裝選項。安裝至系統目錄時，請依作業系統套件管理方式處理所需權限。

## 閱讀操作

- **書架**：顯示書架目錄中的 `.pdb` 和 `.updb` 檔案；點選書名開啟。
- **目錄**：顯示書籍章節；點選章節開始閱讀。
- **閱讀畫面**：使用滑鼠滾輪或以下按鍵翻頁：
  - 上一頁：`Page Up`、`Up`、`k`
  - 下一頁：`Page Down`、`Down`、`Space`、`j`
- 可從字型選項調整書架、目錄與閱讀畫面的字型。

程式會記錄視窗、字型、書架目錄，以及上次閱讀的書籍、章節和頁面。預設書架目錄為 `~/download/`，偏好設定儲存在 `~/.config/pymbook.conf`。

## 授權

pymbook 以 GNU General Public License 第 3 版或更新版本授權。詳見 [COPYING](COPYING)。
