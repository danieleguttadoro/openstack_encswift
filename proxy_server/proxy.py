#!/usr/bin/env python

from flask import *
from werkzeug.exceptions import HTTPException, NotFound

from enc_swift.enc_swiftclient_API import EncSwiftclientAPI as esc
from enc_swift.config import *
from swiftclient.client import ClientException
from werkzeug.serving import WSGIRequestHandler

import requests,json

app = Flask(__name__)                                                            

host = '127.0.0.1'
port = 8801
host_url = 'http://%s:%d' % (host,port)

DENIED_HEADERS = ['Host']

def sanitize_headers(headers):
    return dict((k, v) for k, v in headers.items()
                            if k not in DENIED_HEADERS)
                            
class CustomRequestHandler(WSGIRequestHandler):

    def connection_dropped(self, error, environ=None):
        print 'dropped, but it is called at the end of the execution :('

def change_endpointURL_v2(name, info):
    """
    Change endpoint during authentication version 2
    """
    for el in info['access']['serviceCatalog']:
        if el['name'] == name:
            el['endpoints'][0]['adminURL'] = host_url
            el['endpoints'][0]['publicURL'] = host_url+el['endpoints'][0]['publicURL'][el['endpoints'][0]['publicURL'].find('/v1/')+3:]
            el['endpoints'][0]['internalURL'] = host_url+el['endpoints'][0]['internalURL'][el['endpoints'][0]['internalURL'].find('/v1/')+3:]
            
def change_endpointURL_v3(info):
    """
    Change endpoint during authentication version 3
    """
    try:
      for el in info['token']['catalog']:
        if el['name'] == "swift":
            el['endpoints'][0]['url'] = host_url+el['endpoints'][0]['url'][el['endpoints'][0]['url'].find('/v1/')+3:] 
            el['endpoints'][1]['url'] = host_url+el['endpoints'][1]['url'][el['endpoints'][1]['url'].find('/v1/')+3:]
            el['endpoints'][2]['url'] = host_url
        if el['name'] == "keystone":
            el['endpoints'][0]['url'] = host_url 
            el['endpoints'][1]['url'] = host_url
            el['endpoints'][2]['url'] = host_url
      return True
    except:
        return None

#v3 endpoint
@app.route('/auth/tokens', methods=['POST'])
def authentication_v3():
    req = requests.post('%s/auth/tokens' %(AUTH_URL), stream=True, headers=request.headers, data=request.data)
    info =  json.loads(req.content)
    a = change_endpointURL_v3(info)
    if a == None:
        return Response('',status = 401)
    return Response(response=json.dumps(info), status= req.status_code, content_type = req.headers['content-type'], headers = dict(req.headers))

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get all the information about the user with this id
    """
    head = {}
    head['X-Auth-Token'] = request.headers.get('X-Auth-Token',None)
    req = requests.get('%s/users/%s' %(AUTH_URL,user_id), headers=head)
    return Response(response=req.content, status= req.status_code, content_type = req.headers['content-type'], headers = dict(req.headers))

@app.route('/users')
def get_users(): 
    """
    Get all the infromation about the users
    """
    head = {}
    head['X-Auth-Token'] = request.headers.get('X-Auth-Token',None)
    req = requests.get('%s/users' %(AUTH_URL), headers=head)
    content = json.loads(req.content)
    for i in content.get('users',[]):
        a = i.get('links',{}).get('self','')
        id_ = a[a.find('/users/'):]
        addr = "%s%s" %(host_url,id_)
        i['links']['self'] = addr
    return Response(response=json.dumps(content), status= req.status_code, content_type = req.headers['content-type'], headers = dict(req.headers))

@app.route('/<auth_tenant>/<container>', methods=['POST'])
def post_container(auth_tenant,container):
    """
    Post container function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]

    headval = dict(sanitize_headers(request.headers))
    
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        if headval:
            esc_conn.post_container(container,headval)
        else:
            esc_conn.put_container(container)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    
    return Response(status=200)


@app.route('/<auth_tenant>/<container>', methods=['PUT'])
def put_container(auth_tenant,container):
    """
    Put container function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        esc_conn.put_container(container)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    return Response(status=200)


@app.route('/<auth_tenant>/<container>/<path:path>', methods=['PUT'])
def put_obj(auth_tenant,container,path):
    """
    Put object function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
        path: object naMe with complete path
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
         esc_conn.put_object(container, path, request.data)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)

    return Response(status=200)


@app.route('/<auth_tenant>/<container>', methods=['HEAD'])
def head_cont(auth_tenant,container):
    """
    Head container function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
    """
    auth_tenant = str(auth_tenant)
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        headers = esc_conn.head_container(container)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    
    return Response('', headers = dict(headers))


@app.route('/<auth_tenant>/<container>', methods=['GET'])
def get_cont(auth_tenant,container):
    """
    Get container function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
    """
    _type = request.args.get('format', '')
    _marker = request.args.get('marker', '')
    _prefix = request.args.get('prefix', '')
    _delimiter = request.args.get('delimiter', '')
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        headers, data = esc_conn.get_container(container, delimiter=_delimiter, prefix=_prefix, marker=_marker)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    
    return Response(stream_with_context(json.dumps(data)), headers = dict(headers))


@app.route('/<auth_tenant>/<container>/<path:path>', methods=['HEAD'])
def head_obj(auth_tenant,container,path):
    """
    Head object function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
        path: object naMe with complete path
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        headers = esc_conn.head_object(container, path)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    return Response('', headers = dict(headers))


@app.route('/<auth_tenant>/<container>/<path:path>', methods=['GET'])
def get_obj(auth_tenant,container,path):
    """
    Get object function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
        path: object naMe with complete path
    """
    auth_token = request.headers.get('X-Auth-Token',None)
    cookie = request.headers.get('Cookie',None)
    if auth_token == None and cookie != None:
        auth_token = cookie[cookie.find('id=')+3:]#cookie.split('"')[1]#
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(project_id=project_id,auth_token=auth_token)
        headers, data = esc_conn.get_object(container,path)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    except Exception as err:
        print Exception,err
        return Response(status=404)
    return Response(response = data, headers = headers, status=200)

@app.route('/<auth_tenant>/<container>', methods=['DELETE'])
def delete_cont(auth_tenant,container):
    """
    Delete container function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        esc_conn.delete_container(container)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    
    return Response(status=200)

@app.route('/<auth_tenant>/<container>/<path:path>', methods=['DELETE'])
def delete_obj(auth_tenant,container,path):
    """
    Delete object function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
        path: object naMe with complete path
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        esc_conn.delete_object(container,path)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    except Exception,err:
        return Response(status=304)
    
    return Response(status=200)

@app.route('/<auth_tenant>/<container>/<path:path>', methods=['POST'])
def post_obj(auth_tenant,container,path):
    """
    Post object function
    Args:
        auth_tenant: AUTH_+ project_id
        container: container name
        path: object naMe with complete path
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    headval = dict(sanitize_headers(request.headers))
    
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        esc_conn.post_object(container,path,headval)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    
    return Response(status=200)

@app.route('/<auth_tenant>', methods=['POST'])
def post_account(auth_tenant):
    """
    Post account function
    Args:
        auth_tenant: AUTH_+ project_id
    """
    auth_token = request.headers['X-Auth-Token']
    project_id = auth_tenant[auth_tenant.find('_')+1:]

    headval = dict(sanitize_headers(request.headers))
    
    try:
        esc_conn = esc(auth_token, project_id)
    except Exception as err:
        print err
    try:
        esc_conn.post_account(headval)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    
    return Response(status=200)

@app.route('/<auth_tenant>', methods=['GET'])
def get_account(auth_tenant):
    """
    Get account function
    Args:
        auth_tenant: AUTH_+ project_id
    """
    auth_token = request.headers.get('X-Auth-Token',None)
    project_id = auth_tenant[auth_tenant.find('_')+1:]
    try:
        if auth_token != None:
            esc_conn = esc(auth_token, project_id)
            account_stat, containers = esc_conn.get_account()
            return Response(response=json.dumps(containers),headers = dict(account_stat), status=200)
    except ClientException as exc:
        print exc.http_status
        return Response(status=exc.http_status)
    except Exception as err:
        print Exception, err
    return Response(response="", status=200)
    
if __name__ == "__main__":
    app.run(host=host, port=int(port),debug=True,request_handler=CustomRequestHandler)
