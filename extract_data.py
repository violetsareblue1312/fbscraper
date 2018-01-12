# import libraries
import time

# import web scraping
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
# import webpage parser
from bs4 import BeautifulSoup

from consts import EMAIL, PASSW

SHORT_WAIT = 5

# creates a new webpage and logs into facebook with it
def get_logged_in_driver():
    # set options to prevent chrome alerts
    # open web driver
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications" : 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(chrome_options = chrome_options)

    driver.get("https://www.facebook.com")

    # find and enter email
    elem = driver.find_element_by_id("email")
    elem.clear()
    elem.send_keys(EMAIL)

    # find and enter password
    elem = driver.find_element_by_id("pass")
    elem.clear()
    elem.send_keys(PASSW)

    # loads login page
    elem.send_keys(Keys.RETURN)

    return driver

# returns username as string
# url must be a string of form either
#   '"facebook.com/" + username' or '"facebook.com/" + username + "?" + ...'
# or
#   '"facebook.com/profile.php?id=" + profile_id'
# or
#   '"facebook.com/profile.php?id=" + profile_id + "&" + ....'
def strip_user_name(url):
    if url.find("https://www.facebook.com/profile.php?id=") == 0:
        return strip_id(url)
    start = url.find("facebook.com/")
    end = url.find("?")
    if end == -1:
        end = len(url)
    user_name = url[start + 13 : end]

    return user_name

# returns facebook ID as string
# url must be a string of form either
#   '".php?id=" + ID' or '".php?id=" + ID + "&" + ...'
def strip_id(url):
    start = url.find(".php?id=")
    end = url.find("&")
    if end == -1:
        end = len(url)
    profile_id = url[start + 8 : end]
    return profile_id

# check if facebook account is enabled/disabled and return as Boolean
# Facebook page of user must be loaded (any page)
def extract_enabled(soup):
    if soup.find('span', id = "fb-timeline-cover-name"):
        return True
    else:
        return False

# extracts the profile id number as string
# Facebook page of user must be loaded (any page)
def extract_profile_id(soup):
    tag = soup.find('div', id = "pagelet_timeline_main_column")
    dic = eval(tag['data-gt'])
    profile_id = dic['profile_owner']
    return profile_id

# extracts the username as a string
# Facebook page of user must be loaded (any page)
def extract_username(soup):
    nametag = soup.find('span', id = "fb-timeline-cover-name")
    urltag = nametag.find('a')
    username = strip_user_name(urltag.get('href'))
    return username

# extracts listed name as a string
# Facebook page of user must be loaded (any page)
def extract_name(soup):
    alt_name = extract_altname(soup)
    cover_string = soup.find('span', id = "fb-timeline-cover-name").text
    if alt_name:
        name = cover_string[ : -len(alt_name)]
    else:
        name = cover_string
    return name

# extracts alternate name listed beneath name as string
# Facebook page of user must be loaded (any page)
def extract_altname(soup):
    tag = soup.find('span', class_ = "alternate_name")
    if tag:
        alt_name = tag.text
    else:
        alt_name = ""
    return alt_name

# extracts the intro bio (as string) from left column of main fb page
# main facebook page of user must be loaded
def extract_intro(soup):
    intro_section = soup.find('div', id = "intro_container_id")
    if intro_section != None:
        intro = intro_section.text
    else:
        intro = ""
    return intro

# extracts current city, hometown, and all past cities as list of strings
# Locations tab in About page must be loaded
def extract_cities(soup):
    pagelet = soup.find('div', id = "pagelet_hometown")
    data_list = pagelet.find_all("li")
    citylist = []
    for item in data_list:
        city = item.find("span").text
        info = item.text[len(city):]
        if info:
            citylist.append(info + ": " + city)
        else:
            citylist.append(city)

    return citylist

# extracts work info as list of strings
# Work and Education tab in About page must be loaded
def extract_work(soup):
    work_section = soup.find('div', attrs = {'data-pnref' : 'work'})
    if not work_section:
        return []

    work_items = work_section.find_all('li')

    job_list = []
    for job in work_items:
        urltag = job.find("a")
        if urltag:
            url = " " + urltag.get('href')
        else:
            url = ""
        divitems = job.find_all('div')
        jobdata = []

        #populate jobdata for this fixed job
        for item in divitems:
            if len(item.find_all('div')) == 0 and item.text != "":
                jobdata.append(item.text)

        #append the jobdata to job_list
        if len(jobdata) == 3:
            job_list.append(jobdata[0] + url + " Detais: " + jobdata[1] + " " + jobdata[2])
        elif len(jobdata) == 2:
            job_list.append(jobdata[0] + url + " Details : " + jobdata[1])
        elif jobdata[0] != "No workplaces to show":
            job_list.append(jobdata[0] + url)

    return job_list

# extracts education info as list of strings
# Work and Education tab in About page must be loaded
def extract_edu(soup):
    edu_section = soup.find('div', attrs = {'data-pnref' : 'edu'})
    if not edu_section:
        return []

    edu_items = edu_section.find_all('li')

    school_list = []
    for school in edu_items:
        urltag = school.find("a")
        if urltag:
            url = " " + urltag.get('href')
        else:
            url = ""
        divitems = school.find_all('div')
        schooldata = []

        # populate schooldata for this fixed school
        for item in divitems:
            if len(item.find_all('div')) == 0 and item.text != "":
                schooldata.append(item.text)

        #append schooldata to edulist
        if len(schooldata) == 3:
            school_list.append(schooldata[0] + url + " Details: " + schooldata[1] + " " + schooldata[2])
        elif len(schooldata) == 2:
            school_list.append(schooldata[0] + url + " Details: " + schooldata[1])
        elif schooldata[0] != "No schools to show":
            school_list.append(schooldata[0] + url)

    return school_list

# extracts family members as a list of dictionaries
# each dictionary has keys 'name' and 'relation' and keys 'username' and 'id' when available
# Family tab in About page must be loaded
def extract_family(soup):
    family_list = []
    pagelet = soup.find('div', id = "family-relationships-pagelet")

    if pagelet:

        tag_list = pagelet.find_all('li')

        for tag in tag_list:
            if tag.text != "":
                data = {}
                name_tag = tag.find('span')
                data['name'] = name_tag.text
                url_tag = name_tag.find('a')
                if url_tag:
                    data['username'] = strip_user_name(url_tag.get('href'))
                    data['id'] = strip_id(url_tag.get('data-hovercard'))
                data['relation'] = tag.text[len(data['name']):]
                family_list.append(data)

    return family_list

# extracts relationship information as list of strings
# Family tab in About page must be loaded
def extract_romantic(soup):
    rel_info_list = []
    tag_list = soup.find_all('li', attrs = {'data-pnref' : 'rel'})

    for tag in tag_list:
        rel_info_list.append(tag.text)

    return rel_info_list

# extracts contact info as a dictionary
# dictionary keys will vary depending upon user
# Contact and Basic Info tab in About page must be loaded
def extract_contact(soup):
    condict = {}
    try:
        categories = soup.find('div', id = "pagelet_contact").find_all('span', role = "heading")
    except:
        categories = []

    for head in categories:
        categorydata = []
        if head.text != "Contact Information" and head.text != "Websites and Social Links":
            try:
                for dataline in head.parent.next_sibling.find("li").parent.children:
                    data = dataline.find_all("li")
                    if data:
                        if len(data) == 2:
                            categorydata.append(data[0].text + " " + data[1].text)
                        else:
                            categorydata.append(data[0].text)
                    else:
                        categorydata.append(dataline.text)
            except:
                categorydata.append(head.parent.next_sibling.text)
        if categorydata != []:
            condict[head.text] = categorydata
    return condict

# extracts basic info as dictionary
# dictionary keys will vary depending upon user
# Contact and Basic Info tab in About page must be loaded
def extract_basic(soup):
    basicdic = {}
    try:
        categories = soup.find('div', id = "pagelet_basic").find_all('span', role = "heading")
    except:
        categories = []

    for head in categories:
        if head.text != "Basic Information":
            basicdic[head.text] = [head.parent.next_sibling.text]

    return basicdic

# extracts Details section of bio as string
# Details tab in About page must be loaded
def extract_details(soup):
    bio = soup.find('div', id = "pagelet_bio").find('li').text
    if bio == "No additional details to show":
        bio = ""
    return [bio]

# extracts Quotes section of bio as list of strings
# Details tab in About page must be loaded
def extract_quotes(soup):
    quoteblock = soup.find('div', id = "pagelet_quotes").find('li').find('span')
    quotelist = list(quoteblock.stripped_strings)
    if quotelist == ["No favorite quotes to show"]:
        quotelist = []
    return quotelist

# extracts life events timeline as list of strings
# Life Events tab in About page must be loaded
def extract_milestones(soup):
    about_box = soup.find('div', id = "pagelet_timeline_medley_about")
    head = about_box.find('span', role = "heading")
    year_groups = head.parent.next_sibling
    event_list = []
    for group in year_groups.children:
        for span in group.find_all('span'):
            event_list.append(span.text)
    return event_list

# scrolls to the bottom of the friend list
# Friends page must be loaded to driver
def scroll_friends(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    box_list = soup.find('ul', attrs = {"data-pnref" : "friends"})

    if box_list:
        Bool = True
        while Bool:
            # scroll to bottom of page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # wait
            time.sleep(0.25)
            # load final tag from soup and see if it is the loading image
            soup = BeautifulSoup(driver.page_source, "html.parser")
            box_list = soup.find('ul', attrs = {"data-pnref" : "friends"})
            final_tag = box_list.parent.contents[-1]
            Bool = final_tag.name == 'img'

    return

# extracts the friends currently loaded in browser as list of dictionaries
# dictionary keys are 'name', 'username', and 'id'
# Friends List must be loaded
def extract_friends(soup):
    friendlist = []
    groups = soup.find_all('ul', attrs = {"data-pnref" : "friends"})

    for box_list in groups:
        for box in box_list:
            friend = {}

            urltag = box.find('a')
            urlA = urltag.get('href')
            friend['username'] = strip_user_name(urlA)
            urlB = urltag.get('data-hovercard')
            friend['id'] = strip_id(urlB)

            # jump to next 'a' tag having same href url value
            nametag = urltag.find_next('a', attrs = {'href' : urlA})
            friend['name'] = nametag.text

            # Disabled code below captures the 'Line Bio' beneath the friends name
            #try:
                #friend['Line Bio'] = box.find('ul').text
            #except:
                #pass
            friendlist.append(friend)

    return friendlist

# extracts possible family members as list of dictionaries
# dictionary keys are 'name', 'username', and 'id'
# searches user's last_name via the fb friends page to find potential family
# last_name is chosen as maximal tail substring of full_name not having spaces
# Friends List must be loaded
def extract_possfam(driver, full_name):
    last_name = full_name.split(' ')[-1]
    famlist = []
    groups = []
    try:
        elem = driver.find_element_by_class_name("inputtext")
        elem.clear()
        elem.send_keys(last_name)
        elem.send_keys(Keys.RETURN)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        pagelet = soup.find('div', attrs = {"data-pnref" : "friends.search"})
        groups = pagelet.find_all('ul')
    except:
        pass

    for box_list in groups:
        for box in box_list:
            friend = {}
            urltag = box.find('a')
            urlA = urltag.get('href')
            friend['username'] = strip_user_name(urlA)
            urlB = urltag.get('data-hovercard')
            friend['id'] = strip_id(urlB)

            def has_matching_url(tag):
                return tag.get('href') == urlA and tag != urltag

            friend['name'] = box.find(has_matching_url).text
            # Code below grabs the one-line bio beneath friend's name
            #try:
            #    friend['Line Bio'] = box.find('ul').text
            #except:
            #    None
            famlist.append(friend)

    return famlist

# scrolls to the bottom of the group list on users' fb page
# groups page must be loaded to driver
def scroll_groups_via_profile(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    panel = soup.find('div', attrs = {'aria-role' : "tabpanel"})

    if panel:
        Bool = True
        while Bool:
            # scroll to bottom of page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # wait
            time.sleep(0.25)
            # load final tag from soup and see if it is the loading image
            soup = BeautifulSoup(driver.page_source, "html.parser")
            panel = soup.find('div', attrs = {'aria-role' : "tabpanel"})
            chunk = panel.find('ul')
            final_tag = chunk.parent.contents[-1]
            Bool = final_tag.name == 'img'

    return

# extracts the groups listed on user's page
# extracts only the groups currently loaded in the browser
# returns a list of dictionaries
# dictionary keys are 'Name', 'Username', 'Group ID', and when available 'About'
def extract_groups_via_profile(soup):
    grouplist = []
    panel = soup.find('div', attrs = {'aria-role' : "tabpanel"})
    if panel:
        chunks = panel.find_all('ul')
    else:
        chunks = []

    for box_list in chunks:
        for box in box_list:
            group = {}

            urltag = box.find('a', attrs = {'data-hovercard' : True})
            urlA = urltag.get('href')
            group['Username'] = urlA[8: -1]
            urlB = urltag.get('data-hovercard')
            group['Group ID'] = strip_id(urlB)
            group['Name'] = urltag.text

            count_a = urltag.parent.next_sibling.text
            count_b = count_a.split(' ')[0]
            count_c = count_b.replace(',', '')
            group['Size'] = eval(count_c)

            about_tag = box.find('span')
            if about_tag:
                group['About'] = about_tag.text

            grouplist.append(group)

    return grouplist

# scrolls to the bottom of the group list on search page
# search page with list of groups must be loaded to driver
def scroll_groups_via_search(driver):

    Bool = True
    while Bool:
        # scroll to bottom of page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # wait
        time.sleep(0.25)
        # load final tag from soup and see if it is the loading image
        soup = BeautifulSoup(driver.page_source, "html.parser")
        container = soup.find('div', id = "BrowseResultsContainer")
        penult = container.parent.contents[-2]
        end = penult.find('div', id = "browse_end_of_results_footer")
        if end:
            Bool = False

    return


# extracts the groups listed on facebook search page
# extracts only the groups currently loaded in the browser
def extract_groups_via_search(soup):
    groups = []

    def imggroup(tag):
        return tag.name == 'img' and 'href' in tag.parent.attrs.keys() and tag.parent.get('href').startswith("/groups/")

    content = soup.find('div', id = "contentArea")

    try:
        pictags = content.find_all(imggroup)
    except:
        pictags = []


    for child in pictags:
        tag = child.parent

        group = {}

        greatgrand = tag.parent.parent.parent
        data_bt = greatgrand.get('data-bt')
        start = data_bt.find('"id":')
        data_bt2 = data_bt[start + 5 : ]
        end = data_bt2.find(',')
        group['id'] = data_bt2[ : end]

        url = tag.get('href')
        end = url.find("/?")
        group['url'] = url[8:end]

        # look at next tag with the same url
        nametag = tag.find_next('a', attrs = {'href' : url})
        group['name'] = nametag.text

        for text in tag.next_sibling.stripped_strings:
            parts = text.split(' ')
            if len(parts) >= 2:
                a = parts[0]
                b = parts[1]
                if a.endswith('M'):
                    z = a.find('.')
                    if z == -1:
                        z = len(a) - 2
                    a = a[0: -1] + "0"*(8 + z - len(a))
                    a = a.replace('.', '')
                if a.endswith('K'):
                    z = a.find('.')
                    if z == -1:
                        z = len(a) - 2
                    a = a[0 : -1] + "0" *(5 + z - len(a))
                    a = a.replace('.', '')
                a = a.replace(',' , '')
                if a.isdigit() and (b == "members" or b == "member"):
                    group['size'] = int(a)
                    break

        if 'size' not in group.keys():
            raise Exception("Group membership count not found")

        groups.append(group)

    return groups

# "core" items are those that can be extracted from any page of user's fb account
# "core" items are 'enabled', 'username', 'name', and 'altname'
# returns enabled as Boolean and updates the input dictionary by extracting the "core" items listed in fields
# user's fb page must be loaded (any page)
def check_enabled_and_extract_core(data, soup, fields):
    enabled = extract_enabled(soup)
    if 'enabled' in fields:
        data['enabled'] = enabled
    if enabled == False:
        return False
    if 'username' in fields:
        data['username'] = extract_username(soup)
    if 'name' in fields:
        data['name'] = extract_name(soup)
    if 'altname' in fields:
        data['altname'] = extract_altname(soup)
    return True

def url_to_field_dic():
    d = {}
    d.update({"" : {'intro'}})
    d.update({"/about?section=living" : {"cities"}})
    d.update({"/about?section=education" : {"work", "edu"}})
    d.update({"/about?section=relationship": {"romantic", "family"}})
    d.update({"/about?section=contact-info" : {"contact", "basic"}})
    d.update({"/about?section=bio": {"details", "quotes"}})
    d.update({"/about?section=year-overviews": {"milestones"}})
    d.update({"/friends" : {"friends"}})
    #d.update({"/groups" : {"groups"}})
    # d.update({"/followers" : {"followers"}})
    # d.update({"/map" : {"checkins"}})
    # d.update({"/reviews" : {"reviews"}})
    # d.update({"/likes" : {"likes"}})
    # d.update({"/following" : {"following"}})
    # missing url for events
    return d

# extracts the data types listed in fields for the given user
# returns dictionary with key value 'enabled'
# when 'enabled' = True, dictionary also has items in fields as key values
# driver needs to be logged into facebook
def extract_items_for_user(driver, fields, user):
    data = {}
    need_to_scroll = {"friends", "likes"}

    # first round: Grab
    # 'intro', 'cities', 'work', 'edu', 'romantic', 'family',
    # 'contact', 'basic', 'details', 'quotes', 'milestones', 'friends'
    # when present in fields.
    # Also 'enabled', 'username', 'name', and 'altname' will be grabbed
    # if in fields and anything above is grabbed
    url_dic = url_to_field_dic()

    enabled = None
    for url, able in url_dic.items():
        needed = fields.difference(set(data.keys()))
        items = needed.intersection(able)

        if items and enabled != False:
            driver.get("https://www.facebook.com/" + user + url)
            if enabled == None:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                enabled = check_enabled_and_extract_core(data, soup, fields)
            if enabled:
                for item in items:
                    if item in need_to_scroll:
                        eval("scroll_" + item + "(driver)")
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    data[item] = eval("extract_" + item + "(soup)")
            time.sleep(SHORT_WAIT)


    if 'possfam' in fields and enabled != False:
        driver.get("https://www.facebook.com/" + user + "/friends")
        if enabled == None:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            enabled = check_enabled_and_extract_core(data, soup, fields)
        if enabled:
            if 'name' in data.keys():
                name = data['name']
            else:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                name = extract_name(soup)
            data['possfam'] = extract_possfam(driver, name)
        time.sleep(SHORT_WAIT)

    if 'groups' in fields and enabled != False:
        driver.get("https://www.facebook.com/search/" + user + "/groups")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        if str(soup).find("Sorry, we couldn't understand this search.") != -1:
            enabled = False
        if soup.find('div', id = "empty_result_error"):
            enabled = True
            data['groups'] = []
        container = soup.find('div', id = "BrowseResultsContainer")
        if container:
            enabled = True
            scroll_groups_via_search(driver)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            data['groups'] = extract_groups_via_search(soup)
        time.sleep(SHORT_WAIT)

    if 'enabled' in fields and enabled == None:
        driver.get("https://www.facebook.com/" + user)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        enabled = check_enabled_and_extract_cor(data, soup, fields)
        time.sleep(SHORT_WAIT)

    if 'enabled' in fields:
        data['enabled'] = enabled


    return data














# extracts the ID number of the group
# Facebook page of group must be loaded (any page)
def extract_group_id(soup):
    text = str(soup)
    start = text.find("fb://group/?id=")
    cut = text[start + 15 : ]
    end = cut.find('"')
    myid = cut[ : end]
    return myid

# scrolls to the bottom of membership list in a group
# member list page must be loaded to the driver
def scroll_members_of_group(driver):

    def morepage(tag):
        return tag.name == 'div' and 'class' in tag.attrs.keys() and "morePager" in tag.get('class') and tag.text == "See More"

    Bool = True
    while Bool:
        # scroll to bottom of page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # wait
        time.sleep(0.25)
        # load final tag from soup and see if it is the loading image
        soup = BeautifulSoup(driver.page_source, "html.parser")
        moretag = soup.find(morepage)
        if moretag == None:
            Bool = False

    return

# extracts members of fb group as list of dictionaries
# dictionary keys are 'name', 'username', 'id', and 'details'
# member list page must be loaded
def extract_members(soup):
    def recent_join(tag):
        return tag.name == 'div' and 'id' in tag.attrs.keys() and type(tag['id']) == str and tag['id'].startswith("recently_joined_")

    tags = soup.find_all(recent_join)
    members = []
    for tag in tags:
        data = {}
        data['id'] = tag['id'][ 16 : ]
        urltag = tag.find('a')
        data['username'] = strip_user_name(urltag.get('href'))

        nametag = urltag.find_next('a')
        data['name'] = nametag.text
        data['details'] = nametag.parent.next_sibling.text
        members.append(data)

    return members

def extract_items_for_group(driver, fields, group_id):
    data = {}

    if 'members' in fields:
        driver.get("https://www.facebook.com/groups/" + group_id + "/members")
        scroll_members_of_group(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data['members'] = extract_members(soup)

    return data


def main():
    return


# executes the program when we call it from the command line
if __name__ == "__main__":
    main()