#!/usr/bin/env python3

class CTDISKDownloadTask():
	"""Automate Bulk Download from Chinese Cloud Storage CTDISK"""

	def __init__(self):
		self.ctdiskurl = ""
		self.rooturl = ""
		self.source_html = ""
		self.itemlist_count = 0
		self.itemlist = []
		self.range_first = 0
		self.range_last = 0
		self.tasklist = []
		self.tasklist_count = 0
		self.destination = ""
		self.timeout = 0
		self.failedtasklist = []
		self.failedtasklist_count = 0

		from selenium import webdriver
		self.selChromeOptions = webdriver.ChromeOptions()
		self.selChrome_headless()

	def collect_html(self):
		"""COLLECT RENDERED HTML, DOM IS BAD"""
		from urllib.parse import urlparse
		from selenium import webdriver
		from webdriver_manager.chrome import ChromeDriverManager
		from selenium.webdriver.support.ui import Select
		import time
		self.rooturl = urlparse(self.ctdiskurl).scheme + "://" + urlparse(self.ctdiskurl).hostname
		browser = webdriver.Chrome(ChromeDriverManager().install(),options=self.selChromeOptions)
		browser.get(self.ctdiskurl)
		time.sleep(4) # important! - wait for css to load
		## display 200 links per page
		select = Select(browser.find_element_by_css_selector('#table_files_length > label > select'))
		select.select_by_value("200")
		time.sleep(4) # !important - wait for new file list to load
		## store rendered html for parsing
		self.source_html = browser.page_source
		## go through all pages
		while "paginate_button page-item next disabled" not in self.source_html:
			browser.find_element_by_css_selector('#table_files_next .page-link').click()
			time.sleep(4) # !important - wait for next page to load
			self.source_html = self.source_html + browser.page_source
		browser.quit()

	def parse_html(self):
		"""PARSE HTML AND PRINT TO FILE"""
		import bs4    
		import re
		soup = bs4.BeautifulSoup(self.source_html,"html.parser")
		self.itemlist = soup.find_all('a', href = re.compile(r"^/file/"))
		with open('source.log', 'w',encoding="utf-8") as log:
			for i in self.itemlist:
				print(i,file=log)
			self.itemlist_count = len(self.itemlist)
			print("\n" + str(self.itemlist_count) + " items in download list.",file=log)
		print("\n" + str(self.itemlist_count) + " items in download list.")

	def set_taskrange(self):
		"""ITEM SELECTION, ONLY FOR CLI"""
		if self.itemlist_count > 1:
			print()
			self.range_first = int(input("download FROM #:"))
			self.range_last = int(input("download UPTO AND INCLUDE #:"))    
			while (self.range_first <= 0) or (self.range_first > self.itemlist_count) or (self.range_last <= 0) or (self.range_last > self.itemlist_count) or (self.range_first > self.range_last):
				print()
				print("invalid input. try again...")
				print()
				self.range_first = int(input("download FROM #:"))
				self.range_last = int(input("download UPTO and INCLUDE #:"))
			self.tasklist = self.itemlist[self.range_first-1:self.range_last]
		else:
			self.tasklist = self.itemlist
		self.tasklist_count = len(self.tasklist)
		print("download", self.tasklist_count, "item for this task.")

	def selChrome_headless(self):
		self.selChromeOptions.headless = True

	def selChrome_remove_IncompleteDownload(self):
		import os
		targetdir = os.listdir(self.destination)
		for file in targetdir:
			if file.endswith(".crdownload"):
				os.remove(os.path.join(self.destination, file))

	def selChrome_set_DownloadDirectory(self):
		import os
		self.selChromeOptions.add_experimental_option("prefs", {
		"download.default_directory": self.destination,
		"download.prompt_for_download": False,
		"download.directory_upgrade": True,
		"safebrowsing.enabled": False
		})
		while os.path.exists(self.destination) == False:
			os.mkdir(self.destination)

	def selChrome_count_Timeout(self):
		"""https://stackoverflow.com/a/51949811"""
		import time
		import os
		seconds = 1
		wait = True
		while (wait is True) and (seconds < self.timeout):
			time.sleep(1)
			wait = False
			print(seconds, self.timeout)
			files = os.listdir(self.destination)
			#if nfiles and len(files) != nfiles:
			#	wait = True
			for filename in files:
				if filename.endswith('.crdownload'):
					wait = True
			seconds += 1

	def selChrome_Download(self):
		self.selChrome_remove_IncompleteDownload()
		self.selChrome_set_DownloadDirectory()

		## use logging module to print and write to file at the same time
		import logging
		import sys
		logging.basicConfig(handlers=[logging.FileHandler('task.log', 'w', 'utf-8'),logging.StreamHandler(sys.stdout)], level=logging.INFO, format='%(message)s')

		for num in range(0, self.tasklist_count):
			## filter essential info
			import re
			task_name = re.compile(r"""(?<=>)(.*)(?=<)""")
			task_name = task_name.findall(str(self.tasklist[num]))
			task_name = task_name[0]
			task_link = re.compile(r"""\/file\/[\s\S]*?(?=")""")
			task_link = task_link.findall(str(self.tasklist[num]))
			task_link = task_link[0]
			task_link = self.rooturl + task_link
			currentask_num = num + 1
			logging.info("\ninitiating task %d/%d" %(currentask_num,self.tasklist_count))

			## download operation
			from selenium import webdriver
			from webdriver_manager.chrome import ChromeDriverManager
			import time
			browser = webdriver.Chrome(ChromeDriverManager().install(),options=self.selChromeOptions)
			browser.get(task_link)
			logging.info("file name: %s" %(task_name))
			time.sleep(4) # important! - wait for css to load
			browser.find_element_by_css_selector('#main-content > div > div > div:nth-child(5) > div:nth-child(1) > div.card-body.position-relative > button').click()
			time.sleep(10) # important! wait for connection to be made
			logging.info("starting task %d/%d ...." %(currentask_num,self.tasklist_count))
			### if captcha has been triggered, the following line wont execute, then count as failed download
			self.selChrome_count_Timeout()
			### if mission failed or froze, the program will wait for time out, then count as failed download
			### manual PAUSE then RESUME wont break the program, but timeout is still in place.
			### manual CANCEL will count as failed download. RETRY wont change it.
			browser.quit()

			## download result verification
			import os.path
			filepath = os.path.join(self.destination, task_name)
			if os.path.exists(filepath):
				logging.info("\nTask %d/%d: download completed." %(currentask_num,self.tasklist_count))
			else:
				faileditem_num = str(int(self.range_first) + int(currentask_num) - 1)
				failedtask_entry = "Item #" + faileditem_num + "\n" + "File Name: " + task_name + "\n" + "Download Link: " + task_link + "\n"
				self.failedtasklist.append(failedtask_entry)
				self.failedtasklist_count = len(self.failedtasklist)
				logging.info("\nTask %d/%d: download went wrong. file marked." %(currentask_num,self.tasklist_count))
			self.selChrome_remove_IncompleteDownload()

	def report_taskresult(self):
		## use logging module to print and write to file at the same time
		import logging
		import sys
		logging.basicConfig(handlers=[logging.FileHandler('task.log', 'a', 'utf-8'),logging.StreamHandler(sys.stdout)], level=logging.INFO, format='%(message)s')
		
		# REPORT RESULT		
		logging.info("\n")
		if self.failedtasklist_count > 0:
			logging.info("%d/%d Task Failed." %(self.failedtasklist_count,self.tasklist_count))
			for i in self.failedtasklist:
				logging.info(i)
			logging.info("%d/%d Task Succeeded." %((self.tasklist_count-self.failedtasklist_count),self.tasklist_count))
			logging.info("re-run the program or use the link above to try download again.")
		else:
			logging.info("ALL ASSIGNED TASKS HAS BEEN SUCCESSFULLY COMPLETED!")
			logging.info("item %d to %d of %d has been downloaded." %(self.range_first,self.range_last,self.itemlist_count))
		logging.info("view downloaded file (if any) in -> %s" %self.destination)

	def flush_failure(self):
		"""WIPE RECORD FROM LAST RUN, IMPORTANT FOR GUI NEWTASK WITHOUT REANALYZE"""
		self.failedtasklist = []
		self.failedtasklist_count = 0

if __name__ == '__main__':
	try:
		import sys
		task = CTDISKDownloadTask()
		task.ctdiskurl = sys.argv[1]
		task.collect_html()
		task.parse_html()
		task.set_taskrange()
		task.destination = sys.argv[2]
		task.timeout = int(sys.argv[3])
		task.selChrome_Download()
		task.report_taskresult()
	except:
		print("an error has occured.")