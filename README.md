# Swift client encryption 

Encswift app can put encrypted files on swift. It introduces (optionally) the Over-Encryption, in order to avoid useless change on each file, after a policy change.
In order to start this app you have to start `make run` in swift_browser_client and run `proxy.py` in proxy_server. 

Moreover, if Over-Encryption is activated, a particular version of Swift (encswift_server) has to run on the server. Doing a `vagrant up` in devstack-vagrant-enc folder, this modified version will be loaded.

# Branches
Stable release is in branch __master__

# Features redesigned (OpenStack Swift):
* `Put enc container`: it puts a new container and generates a key for it. The users' catalogs are automatically updated
* `Head enc container`: it retrieves the header of the enc container
* `Post enc container`: it posts new headers for a certain container (paying attention if the user tries to change the acl...). It handles the keys management, mainly from the Surface Layer point of view.
* `Delete enc container`: it deletes a container, removing its key from the catalogs of all the users in the acl, and updating the graph
* `Put enc object`: it retrieves the cipher key of the container, uses it to encrypt the object and puts it in the container
* `Get enc object`: it retrieves the BEL and SEL keys of the container, gets the object from the container and decrypts it.
* `Head enc object`: it retrieves the headers of the enc object 
* `Post enc object`: it posts new headers for an enc object
* `Delete enc object`: it retrieves the cipher key of the container, encrypts the name of the object (so that it can find it) and delete it
* `Create user`: it automatically creates a new Keystone user and her Escudo properties (the meta-container and the catalog)

# Proxy_server:

This folder contains a proxy server. It shows an interface to communicate with it and uses the last version of encswift to apply the encryption functions.

# Swift_browser_client (GUI)

This folder contains a standard version of django swift_browser, to communicate in a easy way with the proxy server.
