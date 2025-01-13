from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import os.path

url = 'https://sites.google.com/site/oasisfoyerstg/univers/ludus/bestiaire'

profile = webdriver.FirefoxProfile()
driver = webdriver.Firefox(firefox_profile=profile)
driver.get(url)
