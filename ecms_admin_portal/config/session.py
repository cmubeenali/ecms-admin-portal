from pymongo import MongoClient
from uuid import uuid1
from datetime import datetime

import logging

def new_session(username):
    mgc=MongoClient()
    try:
        sid=uuid1().__str__()
        db=mgc['ecms_backend']
        sess_modified=datetime.now()
        db.user_auth_info.update_one({'username':username},{'$set':{'sid':sid,'sess_modified':str(sess_modified)}})
        return {'sid':sid,'sess_modified':sess_modified}
    except Exception as err:
        logging.error("SESSION_NEW : "+str(err))
    finally:
        mgc.close()

def validate_session(sid):
    session_info={'sid':None,'_is_logged':False}
    mgc=MongoClient()
    try:
        db=mgc['ecms_backend']
        result = db.user_auth_info.find_one({'sid':sid})
        if result is not None:
            session_info['sid']=result['sid']
            session_info['_is_logged']=True
            session_info['sess_modified']=result['sess_modified']
    except Exception as err:
        logging.error("SESSION_VALIDATE : "+str(err))
    finally:
        mgc.close()
        return session_info

def update_sess_modified(sid,sess_modified):
    mgc=MongoClient()
    try:
        db=mgc['ecms_backend']
        db.user_auth_info.update_one({'sid':sid},{'$set':{'sess_modified':sess_modified}})
    except Exception as err:
        logging.error("SESSION_UPDATE : "+str(err))
    finally:
        mgc.close()