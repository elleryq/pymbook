
all: ui_mainwindow.py

ui_mainwindow.py: mainwindow.ui
	pyside-uic $^ -o $@

testdata:
	wget "http://www.haodoo.net/?M=d&P=D55d.updb" -O D55d.updb
	wget "http://www.haodoo.net/?M=d&P=D55d.pdb" -O D55d.pdb
