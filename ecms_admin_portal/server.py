from werkzeug.routing import Rule, Map
from jinja2 import FileSystemLoader, Environment
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.shared_data import SharedDataMiddleware
from datetime import datetime, timedelta

from ecms_applicant_portal.url_config import url_mod, url_mod_action
from ecms_applicant_portal.config.session import validate_session, update_sess_modified
from ecms_applicant_portal.modules.auth import Auth
from ecms_applicant_portal.modules.dashboard import Dashboard

import logging, os, json, frappe

class App(object):

    def __init__(self):
        self.url_map = Map([
            Rule("/", endpoint="module"),
            Rule('/<mod_name>', endpoint="module"),
            Rule('/<mod_name>/', endpoint="module"),
            Rule('/<mod_name>/<action>', endpoint="module"),
            Rule('/<mod_name>/<action>/', endpoint="module"),
        ])
        try:
            pass
        except Exception as err:
            logging.error("ERROR(APP) : Could not find device db settings file, "+str(err))

        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path), autoescape=True)
        
        f_config=open(os.path.dirname(__file__)+'/config/config.json')
        self.config=json.loads(f_config.read())

    def render_template(self, req, template_name, _ret_vals):
        try:
            _t = self.jinja_env.get_template(template_name)
            response=Response(_t.render(_ret_vals), mimetype='text/html')
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['X-Robots-Tag']='noindex'
            return response
        except Exception as err:
            logging.error('ECMSAP_ERROR(RENDER_TEMPLATE) : '+str(err))
    
    def json_response(self, json_data,status_code=200):
        try:
            response=Response(json.dumps(json_data), mimetype='application/html',status=status_code)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['X-Robots-Tag']='noindex'
            return response
        except Exception as err:
            logging.error('ECMSAP_ERROR(JSON_RESP) : '+str(err))

    def not_found(self, req, args):
        return Response("404 " % args,status=404)    
    
    def auth(self, req, args):
        _auth = Auth()
        return _auth.login(self, req, args)
    
    def home(self, req, args):
        _home = Dashboard()
        return _home.main(self, req, args)

    def init_frappe(self,req):
        try:            
            frappe.init(site=os.environ['FRAPPE_SITE_NAME'])
            frappe.connect(set_admin_as_user=True)
            # frappe.set_user(req.headers['Username'])
        except Exception as err:
            logging.error('ECMSAP_ERROR(INIT_FRAPPE) : '+str(err))
    
    def kill_frappe(self):
        try:
            frappe.destroy()
        except Exception as err:
            logging.error('ECMSAP_ERROR(KILL_FRAPPE) : '+str(err))

    def module(self, req, args):
        try:
            if '_is_logged' in req.session.keys():
                if req.session["_is_logged"] == False:
                    if req.path not in ['/auth/login/','/auth/register/', '/auth/reset-pass/','/auth/login','/auth/register', '/auth/reset-pass']:
                        return self.auth(req, req.args)
            else:
                req.session['_is_logged']=False
                return self.auth(req, req.args)

            _components = url_mod.get(args.get('mod_name'))
            if _components is None:
                _mod=None
            else:
                _mod = _components[0] if _components.__len__() > 0 else None
            if _mod is not None:
                # _mod_path='modules.'+_components[0]+_components[1]  : use this code when multiple packages comes up.
                _mod_action = args.get('action')
                if _mod_action is None:
                    _mod_obj = __import__('ecms_applicant_portal.modules.'+_mod)
                    _mod_obj = getattr(_mod_obj,'modules')
                    for component in _components:
                        _mod_obj = getattr(_mod_obj, component)
                    obj_mod = _mod_obj()
                    return obj_mod.main(self, req, args)
                elif _mod_action is not None:
                    _action = url_mod_action.get(_mod_action)
                    if _action is None:
                        return self.not_found(req, args)
                    elif _action is not None:
                        _mod_obj = __import__('ecms_applicant_portal.modules.'+_mod)
                        _mod_obj = getattr(_mod_obj,'modules')
                        for component in _components:
                            _mod_obj = getattr(_mod_obj, component)
                        obj_mod = _mod_obj()
                        _callable = getattr(obj_mod, _action)
                        return _callable(self, req, args)
            elif _mod is None:
                if req.session['_is_logged']==False:
                    return self.not_found(req, args)
                elif req.session['_is_logged']==True:
                    return self.home(req,args)
        except Exception as err:
            logging.error("Oops!. something went wrong : "+str(err)+",  request args : "+str(args))
            return self.home(req,args)

    def dispatch_request(self, req):
        adapter = self.url_map.bind_to_environ(req.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, endpoint)(req, values)
        except HTTPException:
            return self.home(req, req.args)

    def wsgi_app(self, env, start_resp):
        try:
            request = Request(env)
            sid = request.cookies.get('session_data')
            request.session = validate_session(sid=sid)
            if request.session is not None:
                if 'sess_modified' in request.session:
                    sess_modified = datetime.strptime(request.session['sess_modified'],'%Y-%m-%d %H:%M:%S.%f')
                    last_time=datetime.now() - timedelta(hours=0,minutes=int(self.config['SESSION_TIMEOUT']))
                    if sess_modified < last_time:
                        request.session["_is_logged"] = False
                    else:
                        new_sess_modified=str(datetime.now())
                        request.session['sess_modified']=new_sess_modified
                        update_sess_modified(sid=sid,sess_modified=new_sess_modified)
            
            self.init_frappe(request)
            resp = self.dispatch_request(request)            
            self.kill_frappe()

            if sid is None and request.session['sid'] != None:
                resp.set_cookie('session_data', request.session['sid'],samesite='Strict')
            return resp(env, start_resp)
        except Exception as err:
            logging.error("REQUEST_ERROR : "+str(err))            

    def __call__(self, env, start_resp):
        return self.wsgi_app(env, start_resp)

def make_app():
    app = App()
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/public':  os.path.join(os.path.dirname(__file__), 'public'),
    })
    return app