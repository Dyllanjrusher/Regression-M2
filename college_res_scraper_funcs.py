from bs4 import BeautifulSoup
import requests
import re
def get_urls():
    """returns college results urls and ids"""
    cns_df = pd.read_pickle('cns_df.pkl')
    ids = cns_df['IPEDS_ID'].values
    urls = []
    base = 'http://www.collegeresults.org/collegeprofile.aspx?institutionid='
    for IPEDS_ID in ids:
        urls.append(base + str(IPEDS_ID))
    return urls, ids
def get_soup(url):
    """returns soup, if page not there, returns None"""
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    if 'Error occurred while loading college profile' in str(soup.text):
        return None
    return soup

def get_data(soup, header, data):
    for txt in header:
        data.append(soup.find('td', text=txt).next_sibling.next_sibling.text)
    return data


def get_all_data():
    header = ['Endowment Assets', 'Minority-Serving Institution', 'Average High School GPA Among College Freshmen',
              'Sector', 'Median ACT Composite', 'Percent Admitted', 'In-State Tuition and Fees',
              'Out-of-State Tuition and Fees', 'Average Net Price After Grants', 'Median earnings 10 years after entry',
              'Median debt of completers', '% Pell Recipients Among Freshman', '% Black', '% Latino',
              '% Native American', '% Native Hawaiian/Pacific Islander', '% Asian', '% White', '% Two or More Races',
              '% Other', '% Noresident Aliens', '% Female', '% Male', '% Age 25 and Over',
              '% Part-time', 'First-year retention rate', 'Four-year graduation rate', 'Five-year graduation rate',
              'Six-year graduation rate']
    college_results_data = []
    urls, ids = get_urls()
    i = 1
    for url, ID in zip(urls, ids):
        soup = get_soup(url)
        if soup is None:
            print(url, ID)
            continue
        data = [ID]
        college_results_data.append(get_data(soup, header, data))
        if i % 10 == 0:
            print('page {} done'.format(i))
        i += 1
    return college_results_data
