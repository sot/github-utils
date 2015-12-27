import os
import requests

OAUTH_TOKEN = os.environ['GITHUB_SOT_OAUTH']
HEADER = {'Authorization': 'token {}'.format(OAUTH_TOKEN)}


def get_github_repos(username=None, private=None):
    if username is None:
        result = requests.get('https://api.github.com/user/repos',
                              headers=HEADER, params={'page': 3})
    else:
        result = requests.get('https://api.github.com/users/{}/repos'
                              .format(username),
                              headers=HEADER)
    repos = result.json()

    names = [repo['name'] for repo in repos]
    return names, result


def get_org_repo_names(org='sot'):
    page = 1
    names = []
    while True:
        result = requests.get('https://api.github.com/orgs/{}/repos'
                              .format(org), headers=HEADER,
                              params={'page': page, 'per_page': 100})
        repos = result.json()
        names += [repo['name'] for repo in repos]
        page += 1
        if 'next' not in result.links:
            break
    return names


def get_repo_issues(name):
    result = requests.get('https://api.github.com/repos/sot/{}/issues'
                          .format(name),
                          headers=HEADER, params={'per_page': 100})
    return result.json()


def get_org_issues(org='sot', names=None):
    if names is None:
        names = get_org_repo_names(org)
    n_issues = 0
    for name in names:
        issues = get_repo_issues(name)
        print(name, len(issues))
        n_issues += len(issues)
    return n_issues
