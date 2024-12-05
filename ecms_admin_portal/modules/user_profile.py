import logging,frappe
from pymongo import MongoClient


class UserProfile():
    def main(self,app,req,args):
        resp = {"status": "failed", "message": "Error occurred"}
        try:
            mgc=MongoClient()
            db=mgc['ecms_backend']  
            auth_info = db.user_auth_info.find_one({'sid': req.session.get('sid')})
            user_info = frappe.get_doc('Enrollment', auth_info['username'])
            resp['base_url'] = app.config['FRAPPE_BASE_URL']
            resp['user_info'] = user_info
        except Exception as err:
            logging.error("ECMSAP_ERROR(USR_PFL) : " + str(err))
            frappe.log_error("ECMSAP_ERROR(USR_PFL) : " + str(err))
        finally:
            mgc.close()
            return app.render_template(req, "user_profile.html", resp)