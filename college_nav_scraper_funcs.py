#!/usr/bin/env python
# coding: utf-8

# In[466]:


from bs4 import BeautifulSoup
import requests
import re
import time
import pandas as pd
from selenium import webdriver
import pandas as pd

# In[467]:


from selenium import webdriver
import pandas as pd


# In[468]:


def load_webpage():
    driver = webdriver.Chrome('/usr/bin/chromedriver')
    driver.get('https://nces.ed.gov/collegenavigator/')
    return driver


# In[469]:


def get_search_options(driver):
    el = driver.find_element_by_id('MapWrap')
    options = el.find_elements_by_tag_name('option')
    return options


# In[470]:


def search_for_option(no_pref, option, driver):
    no_pref.click()  # deselect no preference
    option.click()
    bachelors_button = driver.find_element_by_id('ctl00_cphCollegeNavBody_ucSearchMain_chkBach')
    bachelors_button.click()
    search_button = driver.find_element_by_id('ctl00_cphCollegeNavBody_ucSearchMain_btnSearch')
    search_button.click()
    return


# In[471]:


def get_student_pop(driver):
    try:
        student_pop = driver.find_element_by_css_selector(
            "#RightContent > div.dashboard > div > div:nth-child(2) > table > tbody > tr:nth-child(7) > td.srb + td")
        student_pop = re.findall('\d+', student_pop.text.replace(',', ''))[0]
    except:
        student_pop = None
    return student_pop


# In[472]:


def get_college_data_row(driver):
    # right now I just grab the name and student population.
    # ill probably have individual funcs for grabbing each param later.
    college_data_row = []
    name = driver.find_element_by_css_selector(".headerlg").text
    student_pop = get_student_pop(driver)
    student_fac_ratio = find_student_faculty_ratio(driver)
    setting = find_campus_setting(driver)
    IPEDS_ID = get_IPEDS_ID(driver)
    expand_all(driver)
    perc_aid = get_percent_aid(driver)
    religious_aff = get_religious_aff(driver)
    perc_reg_disabled = get_registered_disability_perc(driver)
    full_time_fac, part_time_fac = get_faculty_full_part(driver)
    criminal_offenses, vawa_offenses, arrests, disciplinary_actions = get_college_offense_data(driver)
    avg_default_rate = get_avg_default_rate(driver)
    college_data_row.extend([name, student_pop, student_fac_ratio,
                             setting, IPEDS_ID, perc_aid, religious_aff,
                             perc_reg_disabled, full_time_fac, part_time_fac,
                             criminal_offenses, vawa_offenses, arrests, disciplinary_actions,
                             avg_default_rate])
    print(college_data_row)
    return college_data_row


def get_data_on_page(driver):
    data = []
    rows = driver.find_elements_by_css_selector(".resultsTable > tbody > tr")
    for ix, row in enumerate(rows):
        college_link = (driver
                        .find_elements_by_css_selector(".resultsTable > tbody > tr")[ix]
                        .find_element_by_css_selector("a"))
        college_link.click()
        row = get_college_data_row(driver)
        data.append(row)
        driver.back()
    return data


def next_page(selected_page_num, driver):
    css_addition = ' + a' * selected_page_num
    try:
        driver.find_element_by_css_selector('.colorful' + css_addition).click()
        return True
    except:
        return False


def get_data_for_all_pages(driver):
    data = get_data_on_page(driver)
    page_num = 1
    can_go_to_next_page = next_page(page_num, driver)
    while can_go_to_next_page == True:
        data.extend(get_data_on_page(driver))
        page_num += 1
        can_go_to_next_page = next_page(page_num, driver)
    return data


def get_all_college_data(driver):
    print('test')
    option_ix = 1
    college_data = []
    more_options = True
    while more_options:
        print('Here')
        options = get_search_options(driver)
        no_pref = options[0]
        try:
            option = options[option_ix]
            search_for_option(no_pref, option, driver)
            college_data.extend(get_data_for_all_pages(driver))
            driver.get('https://nces.ed.gov/collegenavigator/')
            option_ix += 1
        except:
            more_options = False
    return college_data


def get_info_table(driver):
    info_table = driver.find_element_by_css_selector('#RightContent > div.dashboard > div')
    return info_table


def find_number(text, c):
    return re.search(r'%s(\d+)' % c, text).group(1)



def find_student_faculty_ratio(driver):
    try:
        info = get_info_table(driver).text
        string = re.search('Student-to-faculty ratio:(.*)', info).group(1)
        ratio = eval(string.strip().replace(' to ', '/'))
        return ratio
    except:
        return None


def find_campus_setting(driver):
    try:
        info = get_info_table(driver).text
        setting = re.search('Campus setting:   (.*)\n', info).group(1)
        return setting
    except:
        return None


def get_IPEDS_ID(driver):
    try:
        url = str(driver.current_url)
        ID = int(find_number(text=url, c='id='))
        return ID
    except:
        return None


def expand_all(driver):
    pointer = driver.find_element_by_css_selector('#RightContent > div.fadeyell > div > a:nth-child(1)')
    pointer.click()
    return


def get_percent_aid(driver):
    table = get_all_table(driver)
    evals = ["re.search('Any student (.*)%', table).group(1).split(' ')[-1]",
             "re.search('\d+,\d+ (.*) —— ——\nGrant or scholarship aid', table).group(1)"]
    for evaluation in evals:
        try:
            aid_perc = eval(evaluation)
            return aid_perc
        except:
            continue
    else:
        return None


def get_religious_aff(driver):
    table = get_all_table(driver)
    try:
        aff = re.search('Religious Affiliation\n(.*)\n', table).group(1)
        return aff
    except:
        return None


def get_registered_disability_perc(driver):
    table = get_all_table(driver)
    try:
        disability_perc = re.search('with office of disability services\n(.*)\n', table).group(1)
        return disability_perc
    except:
        return None


def get_all_table(driver):
    table = driver.find_element_by_css_selector('#RightContent').text
    return table


def get_faculty_full_part(driver):
    table = get_all_table(driver)
    try:
        fac = re.search('\nTotal faculty(.*)\n', table).group(1)
        fac = fac.split(' ')
        full_time = fac[1]
        part_time = fac[2]
        return full_time, part_time
    except:
        return None, None


def get_college_offense_data(driver):
    '''
    Returns criminal_offenses, vawa_offeneses, arrests, disciplinary_actions
    
    
    sum of Criminal_Offenses, VAWA Offenses, Arrests, Disciplinary Actions from 2015,2016,2017.
    Offenses include Murder, Negligent Manslaughter, Rape, Fondling, Incest??,
    Statutory Rape, Robbery, Assault, Burglary, Vehicle Theft, Arson. 
    Vawa Offences are domestic violoence, dating violence, stalking.
    Arrests are for weapons, possesion, drug abuse, liquor law violations.
    Disciplinary are for weapons, possesion, drug abuse, liquor law violations.
    '''
    try:
        table = driver.find_element_by_css_selector(
            '#divctl00_cphCollegeNavBody_ucInstitutionMain_ctl11 > div > table > tbody').text
        table = table.replace('2017', '')
        table = table.replace('2016', '')
        table = table.replace('2015', '')
        nums = [int(num) for num in table if num.isnumeric()]
        criminal_offenses = sum(nums[0:33])
        vawa_offenses = sum(nums[33:42])
        arrests = sum(nums[42:51])
        disciplinary_actions = sum(nums[51:])
        return criminal_offenses, vawa_offenses, arrests, disciplinary_actions
    except:
        return None, None, None, None


def get_avg_default_rate(driver):
    '''Returns avg default rate from 2016, 2015, 2014'''
    table = driver.find_element_by_css_selector('#fedloans').text
    try:
        rates = re.search('Default rate (.*)\nNumber in default', table).group(1).replace('%', '').split(' ')
        rate_nums = [float(rate) for rate in rates]
        avg_rates = sum(rate_nums) / 3
        return round(avg_rates, 2)
    except:
        return None