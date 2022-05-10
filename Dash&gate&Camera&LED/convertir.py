import os

from selenium import webdriver
from time import sleep

#driver = webdriver.Firefox()
driver = webdriver.Firefox(executable_path=r'geckodriver.exe')
path = 'file://' + os.path.realpath('map.html')
driver.get(path)
sleep(1)

driver.get_screenshot_as_file("screenshot.png")
driver.quit()