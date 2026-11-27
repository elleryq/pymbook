# pymbook

pymbook 是一個以 GTK 桌面環境執行的電子書閱讀器，主要用來閱讀 [Haodoo](https://www.haodoo.net) 提供的 PDB/uPDB 書籍檔案。程式讀取本機檔案；不會連線至 Haodoo 搜尋或下載書籍。

## 支援格式

- `.pdb`：Haodoo 傳統文字格式，使用 CP950 編碼。
- `.updb`：Haodoo Unicode 格式。

目前不支援 EPUB、PDF 或其他電子書格式。書籍檔案不包含在此原始碼中。

## 執行需求

執行前需安裝：

- Python 3.8 或更新版本
- GTK 3 與 PyGObject（GTK introspection bindings）
- Pycairo

若從原始碼建置翻譯及桌面項目，另需 `msgfmt`（gettext）和
`intltool-merge`。

## 安裝與啟動

若作業系統仍提供 pymbook 套件，建議使用系統的套件管理器安裝。也可在已安裝上述相依套件的環境中，從原始碼目錄直接啟動：

```sh
./pymbook
```

啟動時開啟指定書籍：

```sh
./pymbook /path/to/book.pdb
```

也可使用 `python3 ./pymbook /path/to/book.updb` 開啟 uPDB。未指定檔案時，可透過「開啟」對話框選擇書籍，或從書架載入書籍。

以原始碼安裝（需具備相依套件與建置工具）：

```sh
python3 -m pip install .
```

系統套件管理器也可用來安裝 GTK 3、PyGObject、Pycairo 及建置工具等原生相依套件。

## 開發與套件建置

執行測試：

```sh
python3 -m unittest discover -v
```

GitHub Actions 會在 pull request 和 `master` 更新時執行測試，並分別建置
Debian `.deb` 與 RPM `.rpm`。套件可從該次 workflow run 的 artifacts 下載。
在 Debian/Ubuntu 環境中，也可於安裝 `debian/control` 列出的建置相依套件後執行：

```sh
dpkg-buildpackage -us -uc -b
```

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
