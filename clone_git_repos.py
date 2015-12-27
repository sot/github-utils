import glob
import os
import subprocess

import requests

OAUTH_TOKEN = os.environ['GITHUB_SOT_OAUTH']
HEADER = {'Authorization': 'token {}'.format(OAUTH_TOKEN)}


def update_repo(name, url):
    print('********* {} {} *********'.format(name, url))
    if os.path.exists(name):
        print 'Updating', name
        os.chdir(name)
        retcode = subprocess.call(['git', 'pull', 'origin'])
        if retcode:
            raise Exception()
        os.chdir('..')
    else:
        print 'Cloning', name
        retcode = subprocess.call(['git', 'clone', url])
        if retcode:
            raise Exception()
    print('\n\n')


def update_github_repos(username=None, private=None):
    if username is None:
        result = requests.get('https://api.github.com/user/repos',
                              headers=HEADER)
    else:
        result = requests.get('https://api.github.com/users/{}/repos'
                              .format(username),
                              headers=HEADER)
    repos = result.json()

    for repo in repos:
        if private is not None and repo['private'] != private:
            continue

        url = repo['ssh_url']
        name = repo['name']
        update_repo(name, url)
        print('\n\n')

print('SOT\n')
update_github_repos('sot')

print('\nMe\n')
update_github_repos(private=True)

print('\nLocal\n')
local_repos = glob.glob('/proj/sot/ska/git/*.git')
for local_repo in local_repos:
    name = os.path.basename(local_repo)[:-4]
    update_repo(name, url=local_repo)
