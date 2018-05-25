# ansible_mediawiki
A ansible modue to talk with a mediawiki API
## Features
* Supports BASIC Auth (Header) and MediaWiki Authentication
* Request and Handle edit Tokens
* Error Handling
* Python2 and Python3 compatible
## Authentication
* You can switch between BASIC Auth and MediaWiki Auth with the parameter 'basicauth'
* "basicauth = True" is for BASIC Auth
* "basicauth = False" is for MediaWiki Auth (Default)
## Examples
### Example in Ansible
* This example works with Basic Auth and creates a new site if the site not exists already.
```yaml
- name: Generating Doku
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Generating Rest Conenction String
      set_fact:
        rest_conn:
          server: "server.fqdn"
          username: "frank"
          ssl_verify: False
          basicauth: True

    - name: Check if Page exists
      wiki_rest:
        connection: "{{ rest_conn }}"
        password: "{{ password }}"
        method: get
        path: "?action=query&prop=revisions&rvprop=content&formatversion=2&titles=Test_Page"
      delegate_to: localhost
      register: wiki_Test_page

    - name: Create Test Page if not exists
      wiki_rest:
        connection: "{{ rest_conn }}"
        password: "{{ password }}"
        method: post
        path: ""
        payload:
          action: edit
          title: "Test_Page"
          text: "{{ lookup('template', 'TestPage.j2') }}"
      delegate_to: localhost
      register: wiki_create_test_page
      when: wiki_test_page.result.content.query.pages[0].pageid is not defined
```
### Example in Python
* You can use this Module without Ansible directly in Python
* This time the module uses MediaWiki Auth with a Bot Account
```python
import mediawiki
import json
username = "Admin@test"
password = "<supersecurepassword>"

# Create a new Instance
restclient = mediawiki.wiki_rest_client("test.fqdn","/api.php","?action=query&meta=tokens&format=json",username,password,True,True,False)
# Get Content of a Page
get = restclient.call('get','?action=query&prop=revisions&rvprop=content&formatversion=2&titles=sandbox4','')
if get.content:
        json= json.loads(get.content.decode())
print(json)
print(restclient)

# Create a new Page
data = dict()
data['action'] = "edit"
data['text'] = '==Allgemein==\nHallo Welt!\nDies ist ein erster Test.'
data['title'] = "Sandbox1"

set = restclient.call('post','',data)
print(set.json())
```
