from __future__ import print_function

import os
import requests

OAUTH_TOKEN = os.environ['GITHUB_SOT_OAUTH']
HEADER = {'Authorization': 'token {}'.format(OAUTH_TOKEN)}
GITHUB_API = 'https://api.github.com'

STANDARD_LABELS = dict([(u'bug', u'fc2929'),
                        (u'duplicate', u'cccccc'),
                        (u'enhancement', u'84b6eb'),
                        (u'invalid', u'e6e6e6'),
                        (u'help wanted', u'159818'),
                        (u'question', u'cc317c'),
                        (u'wontfix', u'ffffff'),
                        (u'Priority-Low', u'fee8c8'),
                        (u'Priority-Medium', u'fdbb84'),
                        (u'Priority-High', u'e34a33'),
                        (u'Ready for Final Review', u'fee8c8')])


def request_results(url, *args, **kwargs):
    """
    Get full set of paged results for a GitHub API request, where
    ``args`` and ``kwargs`` are passed to ``requests.get``.
    """
    page = 1
    results = []

    while True:
        kwargs['params'] = {'page': page, 'per_page': 100}
        kwargs['headers'] = HEADER
        result = requests.get(GITHUB_API + url, *args, **kwargs)
        results = result.json()

        page += 1

        if 'next' not in result.links:
            break

    return results


def get_name(repo):
    return repo['name'] if isinstance(repo, dict) else repo


def get_user_repos(username=None):
    """
    Get user repositories for ``username``.  Default gets repos for the
    owner of the token.

    :param username: string user name
    :returns: list of dict
    """
    if username is None:
        repos = request_results('/user/repos')
    else:
        repos = request_results('/users/{}/repos'
                                .format(username))
    return repos


def get_org_repos(org='sot'):
    """
    Get organization repositories for ``org``.  Default is ``sot``.

    :param org: string org
    :returns: list of dict
    """
    repos = request_results('/orgs/{}/repos'.format(org))
    return repos


def get_repo_issues(repo, owner='sot'):
    """
    Get issues for ``repo`` owned by ``owner``

    :param repo: string repo name or dict with key ``name``
    :param owner: string repo owner
    :returns: list of dict
    """
    issues = request_results('/repos/{owner}/{repo}/issues'
                             .format(owner=owner, repo=get_name(repo)))
    return issues


def get_org_issues(org='sot', repos=None):
    """
    Get issues for organization ``org`` (default='sot') for ``repos``.
    If ``repos`` is not supplied then all repos for that org are queried.

    :param org: string org
    :param repos: list of (string or dict)
    :returns: list of dict
    """
    if repos is None:
        repos = get_org_repos(org)

    issues = []
    for repo in repos:
        issues += get_repo_issues(repo)

    return issues


def get_repo_labels(repo, owner='sot'):
    """
    GET /repos/:owner/:repo/labels

    :param repo: string repo name or dict with key ``name``
    :param owner: string repo owner
    :returns: list of dict
    """
    labels = request_results('/repos/{owner}/{repo}/labels'
                             .format(owner=owner, repo=get_name(repo)))
    return labels


def get_repo_label(repo, name, owner='sot'):
    """
    Get a label ``name`` from ``repo``.

    :param repo: string repo name or dict with key ``name``
    :param name: string label name
    :param owner: string repo owner
    :returns: list of dict
    """
    labels = get_repo_labels(repo, owner)
    for label in labels:
        if label['name'] == name:
            return label

    raise ValueError('no label {} found in {} repo'.format(name, get_name(repo)))


def update_repo_label(repo, name, new_color=None, new_name=None, owner='sot'):
    """
    PATCH /repos/:owner/:repo/labels/:name

    :param repo: string repo name or dict with key ``name``
    :param name: string label name
    :param new_color: string new color (default is no change)
    :param new_name: string new name (default is no change)
    :param owner: string repo owner (default = 'sot')
    :returns: requests response object
    """
    label = get_repo_label(repo, name, owner)

    if new_color is None and new_name is None:
        print('label name:{} repo:{} color:{}'
              .format(name, repo, label['color']))
        return

    if new_color is None or new_name is None:
        if new_color is None:
            new_color = label['color']
        if new_name is None:
            new_name = label['name']

    result = requests.patch(GITHUB_API +
                            '/repos/{owner}/{repo}/labels/{name}'
                            .format(owner=owner, repo=get_name(repo), name=name),
                            headers=HEADER,
                            json={'name': new_name, 'color': new_color})
    return result


def create_repo_label(repo, name, color='808080', owner='sot'):
    """
    POST /repos/:owner/:repo/labels

    :param repo: string repo name or dict with key ``name``
    :param name: string label name
    :param color: string color
    :param owner: string repo owner (default = 'sot')
    :returns: requests response object
    """
    result = requests.post(GITHUB_API +
                           '/repos/{owner}/{repo}/labels'
                           .format(owner=owner, repo=get_name(repo)),
                           headers=HEADER,
                           json={'name': name, 'color': color})
    return result


def print_nonstandard_labels_for_repos(repos, standard_labels=None):
    if standard_labels is None:
        standard_labels = STANDARD_LABELS

    repos = sorted(get_name(repo) for repo in repos)
    for repo in repos:
        labels = get_repo_labels(repo)
        print(get_name(repo), end=': ')
        print([(label['name'], label['color']) for label in labels
               if label['name'] not in standard_labels])


def standardize_repo_labels(repo, owner='sot', standard_labels=None):
    """
    Make repo use a standard set of labels.

    POST /repos/:owner/:repo/labels

    :param repo: string repo name or dict with key ``name``
    :param owner: string repo owner (default = 'sot')
    :param standard_labels: dict of label name:color
    """
    if standard_labels is None:
        standard_labels = STANDARD_LABELS

    labels = get_repo_labels(repo, owner=owner)

    # First fix existing old labels like Enhancement and Bug (downcase and
    # change color).
    for label in labels:
        if label['name'] in standard_labels:
            continue

        if label['name'].lower() in standard_labels:
            new_name = label['name'].lower()
            new_color = standard_labels[new_name]
            print('Updating {} label {} to {} {}'
                  .format(get_name(repo), label['name'], new_name, new_color))
            r = update_repo_label(repo, label['name'],
                                  new_color=new_color, new_name=new_name,
                                  owner=owner)

    # Now make sure all the standard labels are there
    labels = get_repo_labels(repo, owner=owner)
    label_names = set(label['name'] for label in labels)

    for name, color in standard_labels.items():
        if name not in label_names:
            print('Creating label {} {} {} {}'
                  .format(get_name(repo), name, color, owner))
            r = create_repo_label(repo, name, color, owner)


def standardize_labels_for_repos(repos, owner='sot'):
    """
    Make list of ``repos`` use a standard set of labels.

    :param repos: list of string repo name or dict with key ``name``
    :param owner: string repo owner (default = 'sot')
    """
    for repo in repos:
        print('Updating {}'.format(get_name(repo)))
        standardize_repo_labels(repo, owner)
        print('')
