#### ----- LIBRARIES ----- ####
import os
import sys
import time
import random
import shutil
import time
import smtplib
import ssl
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup


#### ----- FUNCTIONS DEFINITION ----- ####

## ----- Core scraping functions ----- ##
def get_profile_info():
    '''Scrape username, number of posts, followers and following. Returns the number of followers and
    a string formatted to be saved as the line of a csv file.'''

    username_xpath = '//*[@id="react-root"]/section/main/div/header/section/div[1]/h1'
    post_xpath = '//*[@id="react-root"]/section/main/div/header/section/ul/li[1]/span/span'
    followers_xpath = '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a/span'
    following_xpath = '//*[@id="react-root"]/section/main/div/header/section/ul/li[3]/a/span'

    username_element = driver.find_element_by_xpath(username_xpath)
    post_element = driver.find_element_by_xpath(post_xpath)
    followers_element = driver.find_element_by_xpath(followers_xpath)
    following_element = driver.find_element_by_xpath(following_xpath)

    username = username_element.get_attribute('innerText')
    post = post_element.get_attribute('innerText').replace(',', '')
    followers = followers_element.get_attribute('innerText').replace(',', '')
    following = following_element.get_attribute('innerText').replace(',', '')

    print('Scraping metadata for %s...'% username)

    time.sleep(random.randint(1,3))

    string = username + ',' + post + ',' + followers + ',' + following

    return int(followers), string

def get_followers_list():
    '''Parse the html of the page to get list of followers - and a lot of html rubbish. Then iterate through
    the list to clean up the rubbish and add the usernames to a set. Return the set as a list.'''

    # Parse the html of the page
    followers_list_xpath = '/html/body/div[3]/div/div/div[2]/ul/div'
    followers_list_element = driver.find_element_by_xpath(followers_list_xpath)
    followers_list_html = followers_list_element.get_attribute('innerHTML')
    followers_list_parsed = BeautifulSoup(followers_list_html, "html.parser").find_all('a')

    # Save the list of followers in a set
    followers_set = set()

    for follower in followers_list_parsed:
        username = follower.get('href').replace('/', '')
        followers_set.add(username)

    print('\nFollowers list returned succesfully!')

    return list(followers_set)

def profile_scraper(username):
    '''Wrapper for the bunch of functions that together scrape the profile, write the metadata
    and returns a list of followers'''

    go_to_profile(username)

    n_followers, profile_info = get_profile_info()
    write_metadata(profile_info)

    print('-'*30)

    followers_window = get_followers_window()
    scroll_followers_window(n_followers, followers_window)
    followers_list = get_followers_list()

    print('-'*30)

    return followers_list

## ----- Browser related functions ----- ##
def start_browser():
    '''Initiates a browser window and load instagram.com'''

    driver_path = '/Users/andrea/Desktop/Instagram/chromedriver'
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.set_window_size(1000,1000)
    driver.get("https://www.instagram.com/accounts/login/")

    print('-'*30)
    print('Starting browser...')

    time.sleep(10)

    print('Browser started succesfully!')

    return driver

def login(username, password):
    '''Login to instagram with the given credentials'''

    # Fill in username
    user_box = driver.find_element_by_name("username")
    user_box.click()
    user_box.send_keys(username)

    time.sleep(random.randint(1,5))

    # Fill in password
    psw_box = driver.find_element_by_name("password")
    psw_box.click()
    psw_box.send_keys(password)

    time.sleep(random.randint(1,5))

    # Click login button
    login_button_xpath = '//*[@id="react-root"]/section/main/div/article/div/div[1]/div/form/div[3]'
    login_button = driver.find_element_by_xpath(login_button_xpath)
    login_button.click()

    print('Logging in to instagram...')

    time.sleep(random.randint(1,5))

def go_to_profile(username):
    '''Go to the profile page of a given user'''

    print('Loading the profile of %s...'% username)

    driver.get('https://www.instagram.com/' + username)

    time.sleep(2)

def get_followers_window():
    '''Click on the follower button and return the follower window element'''

    followers_button_xpath = '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]'
    followers_window_xpath = '/html/body/div[3]/div/div/div[2]'

    followers_button_element = driver.find_element_by_xpath(followers_button_xpath)
    followers_button_element.click()

    time.sleep(random.randint(1,3))

    followers_window_element = driver.find_element_by_xpath(followers_window_xpath)

    print('Getting followers window...')

    return followers_window_element

def scroll_followers_window(n_followers, followers_window):
    '''Use a js script to scroll the followers window until the end, so that the names of all the followers
    are loaded in the html of the page'''

    initial_scroll_height = 100
    scroll_height = initial_scroll_height
    n_followers_loaded = 0
    n_followers_constant = 0

    followers_list_xpath = '/html/body/div[3]/div/div/div[2]/ul/div'

    while n_followers_loaded < n_followers:

        # Build and execute the js script
        script = "arguments[0].scrollTop = " + str(scroll_height)
        driver.execute_script(script, followers_window)

        # Save the number of followers loaded before this iteration
        n_followers_loaded_before = n_followers_loaded

        # Update the number of followers loaded
        followers_list_element = driver.find_element_by_xpath(followers_list_xpath)
        followers_list_html = followers_list_element.get_attribute('innerHTML')
        followers_list_parsed = BeautifulSoup(followers_list_html, "html.parser")
        n_followers_loaded = len(followers_list_parsed.find_all('li'))

        # Count for how many iterations the number of followers loaded has remained constant
        if n_followers_loaded_before == n_followers_loaded:
            n_followers_constant += 1
        else:
            n_followers_constant = 0

        # Break the while loop if the number of followers has remained constant for too long
        if n_followers_constant > 100:
            write_error(kind='timeout')
            break

        # Increase scroll height. Start slowly, increase speed after some iterations
        if scroll_height <= 1000:
            scroll_height = scroll_height + random.randint(50, 150)
        else:
            scroll_height = scroll_height + random.randint(500, 1500)

        sys.stdout.write('\rScrolling followers window: %s of %s followers currently loaded.' % (n_followers_loaded, n_followers))

        time.sleep(random.randint(1,3))

## ----- Gephi related functions ----- ##
def merge_all_csv():
    '''Read all the single csv files scraped and merge them all in a single dataframe'''

    csv_names_list = os.listdir(cwd + '/data/followers')
    merged_df = pd.DataFrame(columns=['followers', 'username'])

    for csv in csv_names_list:
        temp_df = pd.read_csv(cwd + '/data/followers/%s' %csv)
        merged_df = pd.concat([merged_df, temp_df], axis=0)

    merged_df.reset_index(drop=True, inplace=True)

    return merged_df

def create_mapping_dict(df):
    '''Create a dictionary that maps every username to a unique ID'''

    unique_username_list = list(set(list(df.followers) + list(df.username)))
    unique_id_list = list(range(0,len(unique_username_list)))

    mapping_dict = dict(zip(unique_username_list, unique_id_list))

    return mapping_dict

def create_edges_df(df, mapping_dict):
    '''Takes the merged dataframe and creates a new one containing the set of edges ready for Gephy.
    The usernames are mapped to integers, as specified in the mapping dictionary.'''

    mapped_username_serie = df.username.map(mapping_dict)
    mapped_followers_serie = df.followers.map(mapping_dict)

    edges_df_anonim = pd.concat([mapped_followers_serie, mapped_username_serie], axis=1)
    edges_df_anonim.columns = ['Source', 'Target']
    edges_df = df.copy(deep=True)
    edges_df.columns = ['Source', 'Target']

    return edges_df, edges_df_anonim

def create_nodes_df(mapping_dict):
    '''Takes the mapping dictionary and the metadata csv and creates a dataframe with information on the nodes
    ready for Gephy'''

    nodes_df = pd.DataFrame(list(mapping_dict.items()), columns=['Label', 'ID'])

    metadata = pd.read_csv(cwd + '/data/metadata.csv')
    metadata['is_my_follower'] = 1

    nodes_df = pd.merge(nodes_df, metadata, how='left', left_on='Label', right_on='username')
    nodes_df.is_my_follower.fillna(0, inplace=True)
    nodes_df.drop('username', axis=1, inplace=True)

    nodes_df_anonim = nodes_df.copy(deep=True)

    nodes_df['ID'] = nodes_df['Label']
    nodes_df_anonim['Label'] = nodes_df['ID']

    return nodes_df, nodes_df_anonim

def prepare_data_for_gephy():
    '''Takes the raw data saved by the scraper and create nodes and edges dataframes ready to be processed in Gephy'''

    merged_df = merge_all_csv()
    mapping_dict = create_mapping_dict(merged_df)

    edges_df, edges_df_anonim = create_edges_df(merged_df, mapping_dict)
    nodes_df, nodes_df_anonim = create_nodes_df(mapping_dict)

    edges_df.to_csv(cwd + '/data/edges.csv', index=False)
    nodes_df.to_csv(cwd + '/data/nodes.csv', index=False)

    edges_df_anonim.to_csv(cwd + '/data/edges_anonim.csv', index=False)
    nodes_df_anonim.to_csv(cwd + '/data/nodes_anonim.csv', index=False)

    print('All done!')

## ----- App specific functions ----- ##
def welcome():
    '''Print a few welcoming lines of code <3'''

    print(
    '''
       `-:::::::::::::::::::.
    `odNNNNNNNNNNNNNNNNNNNNNNNy-
    .mNNNNNmhysssoooossssydNNNNNNo
    yNNNNh:`-/++++++++++/:..oNNNNN`    `...`      ``.``    ```````        ```     ```````    ````````
    hNNNy -dNNNNNNNNNNNNo+do :NNNN-  -hNMMNd+   `odNMNdo`  smmmmmmh/     .mmm`    smmmmmds.  mmmmmmmm+
    hNNN- hNNNNh+::::/yd//dN. dNNN- `NMo::+NM+ `hMmo/+mMd` yMm+++yMM:    yMMMs    yMm++omMd  MMy+++++-
    hNNN. dNNN/`:yddho`.dNNN: hNNN- -MM:.  :+: +MM-   .hh- yMh    NMo   -MM+MN.   yMd   /MM` MM+`````
    hNNN. mNNs :NNNNNNh -NNN: hNNN-  hMMmdyo-  hMd         yMmoooyMd.   hMy dMs   yMm::/dMm  MMmddddd
    hNNN. mNNy -mNNNNNs :NNN: hNNN-  `-+yhmMMy hMd         yMNdddNMs   -MM/.oMM.  yMMNNNmh-  MMhooooo
    hNNN. dNNNs..+syo:`/mNNN- hNNN- -oo   `+MM`oMM.   -dh. yMh```+MM.  hMMNNNMMy  yMd....    MM+
    hNNN: yNNNNmyo//+sdNNNNN` mNNN- .NMs:::hMd `dMm+:+mMh  yMh   -MM- :MM+:::sMM. yMd        MMhooooo/
    hNNNh`.ymNNNNNNNNNNNNNh/ +NNNN.  -hmMMMms.  `smMMMmo`  smy   .mm/ ymy    `dmo smy        mmmmmmmmy
    sNNNNm+-..----------.../hNNNNN`    `...`      `...`    ```    ``` ```     ``` ```        `````````
    `hNNNNNNmmdddhhhhddddmNNNNNNm:
     :sdNNNNNNNNNNNNNNNNNNNNmh+`
        ``````````````````                                                                           '''
    )

    print('\nWelcome to the instagram followers scraping tool!\n')
    print('github.com/andreatondella/instagram_scraper\n')
    print('Copyright (c) 2019 Andrea Tondella')
    print('This script is licensed under the MIT license')

    time.sleep(1)

def create_space():
    '''Delete the folders and the files if they already exist - from previous interrupted iterations.
    Then recreate the folders, the log and the metadata files. Finally return the cwd'''

    cwd = os.getcwd()

    if os.path.exists(cwd + '/data'):
        shutil.rmtree(cwd + '/data')

    os.makedirs(cwd + '/data')
    os.makedirs(cwd + '/data/followers')

    metadata_header = 'username,n_post,followers,following'
    metadata = open(cwd + '/data/metadata.csv', 'a+')
    metadata.write(metadata_header + '\n')
    metadata.close()

    log_header = 'Log file that collects the username off all those user that raised an error while scraping'
    log = open(cwd + '/data/log.txt', 'a+')
    log.write(log_header + '\n')
    log.close()


    print('Folders and files necessary for the app have been created succesfully.\n')

    return cwd

def get_credentials():
    '''Get username and password of the user that will be analyzed.'''

    print('Please provide your credentials to access instagram:')

    username = input('Username: ')
    password = input('Password: ')

    return username, password

def write_metadata(profile_info):
    '''Write the profile info in a file called metadata.csv'''

    metadata = open(cwd + '/data/metadata.csv', 'a+')
    metadata.write(profile_info + '\n')
    metadata.close()

    print('Metadata saved succesfully!')

def save_my_df(my_followers_list, my_username):
    '''Save the df of my own followers to a .csv file'''

    path = cwd + '/data/followers/' + my_username + '.csv'
    my_followers_df = pd.DataFrame({'followers': my_followers_list, 'username':[my_username]*len(my_followers_list)})
    my_followers_df.to_csv(path, index=False)

    print('The list of your followers has been saved.')
    print('You can access it at: %s' % path)
    print('-'*30)
    print("Time to go take a look at the profile of your followers, let's start!\n")

def save_user_df(user_followers_list, username):
    '''Save the df of a user followers to a .csv file'''

    path = cwd + '/data/followers/' + username + '.csv'
    user_followers_df = pd.DataFrame({'followers': user_followers_list,
                                      'username': [username]*len(user_followers_list)})

    user_followers_df.to_csv(path, index=False)

    print('The list of %s followers has been saved.'% username)
    print('You can access it at: %s' % path)
    print('-'*30)

def write_error(kind):
    '''Write the username that raised an error in a file called log.txt'''

    log = open(cwd + '/data/log.txt', 'a+')

    if kind == 'timeout':
        log.write('Timeout Error with user %s\n' %username)
    if kind == 'general':
        log.write('General Error with user %s\n' %username)

    log.close()

    print('\n' + '-'*30)
    print('There has been an error with user %s. His name has been saved in log.txt' %username)
    print('-'*30)

def sleep(username, n_user_scraped, n_user):
    '''Take a break between 1 and 5 minutes before moving to the next user.'''

    random_time = random.randint(10,30)
    n_user_to_scrape = n_user - n_user_scraped

    print('The scraping of %s followers is finished.' % username)
    print('%s followers remaining' %n_user_to_scrape)


    while random_time > 0:
        sys.stdout.write('\rSleeping for %s seconds...' % random_time)
        time.sleep(1)
        random_time -= 1

    sys.stdout.write('\rMoving on to the next user...\n')

    time.sleep(1)

def send_email(kind):
    '''Send email updates and notice when the script has finished'''

    # Email server settings
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "Your_sender_email@gmail.com"
    password = "Your_sender_password"
    receiver_email = "Your_receiver_email@gmail.com"
    context = ssl.create_default_context()

    # Computing time elapsed by the script
    elapsed_time = time.time() - start_time
    elapsed_time_formatted = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

    # Message Creation
    if kind == 'start':
        message = 'Subject: Update from your Raspberry: starting\n\n' + \
                'Hola!\n\nI just started scraping your followers here. ' + \
                'I have ' + str(len(my_followers_list)) + ' profiles to look at.' + \
                '\nI will keep you updated!\n\nWith <3\nInstagram Scraper'

    if kind == 'update':
        message = 'Subject: Update from your Raspberry: ongoing\n\n' + \
                'Hola!\n\nI am still scraping your followers here, ' + \
                'so far I have looked at ' + str(n_user_scraped) + \
                ' and it took me ' + elapsed_time_formatted + \
                '.\n' + 'I will keep you updated!\n\nWith <3\nInstagram Scraper'

    if kind == 'finish':
        message = 'Subject: Update from your Raspberry: finished!\n\n' + \
                'Hola!\n\nI am happy to announce you that I have finished ' + \
                'scraping your followers, ' + \
                ' and it took me ' + elapsed_time_formatted + \
                '.\n' + 'The files are here waiting for you:\n\nWith <3\nInstagram Scraper'

    # Send email
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

def print_header(username):
    '''Display a pretty header when starting to scrape a new user'''

    print(' _____________________' + '_'*len(username))
    print('|                     ' + ' '*len(username) + '|')
    print('| SCRAPING NEW USER: %s |'%username)
    print('|_____________________' + '_'*len(username) + '|' + '\n')


#### ----- TIME FOR SOME SCRAPING! ----- ####

## ----- STEP 1: Initialize directories, start browser and get credentials to login into instagram ----- ##
welcome()

cwd = create_space()

my_username, password = get_credentials()

start_time = time.time()

driver = start_browser()

login(my_username, password)

## ----- STEP 2: scrape my own profile to get a list of my followers ----- ##
my_followers_list = profile_scraper(my_username)

save_my_df(my_followers_list, my_username)

## ----- STEP 3: scrape the profile of my followers to get lists of their followers ----- ##
send_email(kind='start')

n_user_scraped = 0
my_followers_list = my_followers_list[0:2]
for username in my_followers_list:

    print_header(username)

    try:
        user_followers_list = profile_scraper(username)
        save_user_df(user_followers_list, username)

    except:
        write_error(kind='general')

    n_user_scraped += 1

    # Send email updates every 50 followers scraped
    if n_user_scraped % 50 == 0:
        try:
            send_email(kind='update')
        except:
            pass

    sleep(username, n_user_scraped, len(my_followers_list))

## ----- STEP 4: close the browser, prepare the data in a gephi-friendly format and close the app ----- ##
driver.close()

prepare_data_for_gephy()

send_email(kind='finish')
