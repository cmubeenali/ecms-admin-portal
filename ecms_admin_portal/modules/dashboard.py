
import logging, frappe

class Dashboard():
    def main(self,app,req,args):
        try:
            pass
        except Exception as err:
            logging.error('ECMSAP_ERROR(DASH) : '+str(err))
            frappe.log_error('ECMSAP_ERROR(DASH) : '+str(err))
        finally:
            return app.render_template(req,'dashboard.html',{})