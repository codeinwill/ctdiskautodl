#!/usr/bin/env python3

from ctdiskautodl import CTDISKDownloadTask
"""GUI (graphical user interface) for ctdiskautodl"""

import sys
from PyQt5 import QtWidgets
from MainWindow import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self, *args, obj=None, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)
		self.setupUi(self)

App = QtWidgets.QApplication(sys.argv)
Window = MainWindow()

readme = open('README.md').read()
Window.response_shell.setPlainText(readme)
task = CTDISKDownloadTask()

def analyze_url():
	try:
		task.ctdiskurl = Window.ctdiskurl_value.text()
		task.collect_html()
		task.parse_html()
		log = open('source.log', encoding="utf8").read()
		Window.response_shell.setPlainText(log)
		Window.response_shell.verticalScrollBar().setValue(Window.response_shell.verticalScrollBar().maximum())
		enable_other()
	except:
		Window.response_shell.setPlainText("analyze_url: an error has occured.")
		disable_other()
Window.button_analyze.clicked.connect(analyze_url)

def disable_other():
	Window.destination_value.setEnabled(False)
	Window.destination_value_choosedir.setEnabled(False)
	Window.itemnum_value_first.setEnabled(False)
	Window.itemnum_value_last.setEnabled(False)
	Window.timeout_value.setEnabled(False)
	Window.response_savetofile.setEnabled(False) 
	Window.button_download.setEnabled(False)

def enable_other():
	Window.destination_value.setEnabled(True)
	Window.destination_value_choosedir.setEnabled(True)
	Window.itemnum_value_first.setEnabled(True)
	Window.itemnum_value_last.setEnabled(True)
	Window.itemnum_value_first.setMaximum(task.itemlist_count)
	Window.itemnum_value_last.setMaximum(task.itemlist_count)
	Window.timeout_value.setEnabled(True)
	Window.response_savetofile.setEnabled(True)

def get_destination():
	task.destination = QtWidgets.QFileDialog.getExistingDirectory()
	if '/' in task.destination:
		task.destination = task.destination.replace('/','\\') #!important
	Window.destination_value.setText(task.destination)
	Window.button_download.setEnabled(True)
Window.destination_value_choosedir.clicked.connect(get_destination)

def get_tasklist():
	task.range_first = Window.itemnum_value_first.value()
	task.range_last = Window.itemnum_value_last.value()
	task.tasklist = task.itemlist[task.range_first-1:task.range_last]
	task.tasklist_count = len(task.tasklist)

def get_timeout():
	task.timeout = Window.timeout_value.value()

def download():
	try:
		get_tasklist()
		get_timeout()
		task.selChrome_Download()
		task.report_taskresult()
		log = open('task.log', encoding="utf8").read()
		Window.response_shell.setPlainText(log)
		Window.response_shell.verticalScrollBar().setValue(Window.response_shell.verticalScrollBar().maximum())
		task.flush_failure()
	except:
		Window.response_shell.setPlainText("download: an error has occured.")
		disable_other()
Window.button_download.clicked.connect(download)

def save():
	try:
		filename = QtWidgets.QFileDialog.getSaveFileName(filter="Text (*.txt)")
		if filename != ('', ''): #!important - without this will cause error if cancel because of empty filename
			with open(filename[0], 'wb') as file:
				log = Window.response_shell.toPlainText()
				file.write(log.encode('utf8'))
	except:
		Window.response_shell.setPlainText("save: an error has occured.")
Window.response_savetofile.clicked.connect(save)


Window.show()
App.exec()
App.quit()