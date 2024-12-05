import logging,frappe

class Example():
    def main(self,app,req,args):
        resp = {"status": "failed", "message": "Error occurred"}
        try:
            pass
        except Exception as err:
            logging.error("ECMSAP_ERROR(EXAMPLE) : " + str(err))
            frappe.log_error("ECMSAP_ERROR(EXAMPLE) : " + str(err))
        finally:
            return app.render_template(req, "example_page.html", resp)