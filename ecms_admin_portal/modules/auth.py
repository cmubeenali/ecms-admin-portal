from datetime import datetime

from werkzeug.utils import redirect
from werkzeug.wrappers import Response
from pymongo import MongoClient

from frappe.utils.background_jobs import enqueue
from frappe.exceptions import DoesNotExistError
from frappe.core.doctype.user.user import User

from cms_web.consultancy_management_portal.doctype.enrollment.enrollment import (
    generate_password,
)
from ecms_admin_portal.config.session import new_session

import json, os, io, frappe, logging


class Auth:
    def login(self, app, req, args):
        resp = {
            "status": "success",
            "message": "Oops!. Error occurred, we are sorry for your inconvenience.",
        }
        try:
            if req.form:
                mgc = MongoClient()
                db = mgc["ecms_backend"]
                user_info = db.user_auth_info.find_one(
                    {
                        "username": req.form.get("username"),
                    }
                )
                if user_info is not None:
                    doc_user= User.find_by_credentials(user_name=str(req.form.get("username")).strip(),password=req.form.get("password"))
                    if doc_user is None:
                        resp["status"] = "failed"
                        resp["message"] = "Invalid username or password"
                    elif doc_user is not None:
                        if not doc_user.is_authenticated:
                            resp['message']='Invalid login credentials'
                        else:        
                            sess_info = new_session(req.form.get("username"))
                            logged_resp = redirect("/dash", code=302)
                            logged_resp.set_cookie(
                                "session_data", sess_info["sid"], samesite="Strict"
                            )
                            return logged_resp
                elif user_info is None:
                    resp["status"] = "failed"
                    resp["message"] = "Invalid username or password"
                mgc.close()
        except Exception as err:
            logging.error("ECMSAP_ERROR(AUTH_LOGIN) : " + str(err))
            frappe.log_error("ECMSAP_ERROR(AUTH_LOGIN) : " + str(err))

        return app.render_template(req, "login.html", resp)    

    def logout(self, app, req, args):
        try:
            mgc = MongoClient()
            db = mgc["ecms_backend"]
            db.user_auth_info.update_one(
                {"sid": req.session.get("sid")}, {"$set": {"sid": None}}
            )

            return redirect("/auth/login")

        except Exception as err:
            logging.error("ECMSAP_ERROR(AUTH_REG) : " + str(err))
            frappe.log_error("ECMSAP_ERROR(AUTH_REG) : " + str(err))
        finally:
            mgc.close()

    def change_password(self, app, req, args):
        resp = {"status": "failed", "message": "error occurred"}
        try:
            if req.method == "POST":
                try:
                    data = json.loads(req.data.decode("utf-8"))
                    mgc = MongoClient()
                    db = mgc["ecms_backend"]
                    auth_info = db.user_auth_info.find_one(
                        {"sid": req.session.get("sid")}
                    )
                    old_password = data.get("oldPassword")
                    if auth_info and auth_info["password"] == old_password:
                        new_password = data.get("newPassword")
                        db.user_auth_info.update_one(
                            {"sid": req.session.get("sid")},
                            {"$set": {"sid": None, "password": new_password}},
                        )
                        resp["status"] = "success"
                        resp["message"] = "Password changed successfully."
                        return app.json_response(resp)
                    else:
                        resp["status"] = "failed"
                        resp["message"] = (
                            "Incorrect old password or user does not exist."
                        )
                        return app.json_response(resp)
                except Exception as err:
                    logging.error("ECMSAP_ERROR(Change_Password) : " + str(err))
                    frappe.log_error("ECMSAP_ERROR(Change_Password) : " + str(err))
                finally:
                    mgc.close()
            else:
                return app.render_template(req, "change_password.html", resp)

        except Exception as err:
            logging.error("ECMSAP_ERROR(Change_Password) : " + str(err))
            frappe.log_error("ECMSAP_ERROR(Change_Password) : " + str(err))

    def reset_password(self, app, req, args):
        resp = {"status": "pending", "message": "error occurred"}
        try:
            if req.method == "POST" and req.form:
                username = req.form.get("userName")
                try:
                    user_info = frappe.get_doc("Enrollment", username)
                    if user_info:
                        email_id = user_info.email_id

                        mgc = MongoClient()
                        db = mgc["ecms_backend"]
                        auth_info = db.user_auth_info.find_one({"username": username})
                        if auth_info:
                            new_password = generate_password()
                            db.user_auth_info.update_one(
                                {"username": username},
                                {
                                    "$set": {
                                        "password": new_password,
                                        "sid": None,
                                        "sess_modified": str(datetime.now()),
                                    }
                                },
                            )
                            pwd_path = os.environ["PWD"].split("/")
                            # Remove the last element and directly join the remaining parts into a path
                            file_path = (
                                "/".join(pwd_path[:-1])
                                + "/apps/cms_web/cms_web/templates/email_template.html"
                            )

                            # Read the HTML template file from the specified path
                            try:
                                with open(file_path, "r") as file:
                                    html_template = file.read()
                            except Exception as err:
                                frappe.log_error(
                                    "ECMSAP_ERROR(AUTH_FORGT_PASS) : " + str(err)
                                )
                                logging.error(
                                    "ECMSAP_ERROR(AUTH_FORGT_PASS) : " + str(err)
                                )

                            html_resp = html_template.format(
                                first_name=user_info.first_name,
                                last_name=user_info.last_name,
                                user_name=username,
                                password=new_password,
                                current_year=datetime.now().year,
                            )
                            email_args = {
                                "recipients": email_id,
                                "subject": "Your Password Details",
                                "message": html_resp,
                            }
                            enqueue(
                                method=frappe.sendmail,
                                queue="short",
                                timeout=300,
                                is_async=True,
                                **email_args,
                            )

                            resp["status"] = "success"
                            resp["message"] = (
                                f"New password has been sent to your mail : {email_id}. Please change the sent password once logged in."
                            )

                        mgc.close()
                    else:
                        resp["status"] = "failed"
                        resp["message"] = (
                            "No details found for the provided username. Please verify your input and try again."
                        )
                except DoesNotExistError as err:
                    resp["status"] = "failed"
                    resp["message"] = err

        except Exception as err:
            logging.error("ECMSAP_ERROR(AUTH_FORGT_PASS) : " + str(err))
            frappe.log_error("ECMSAP_ERROR(AUTH_FORGT_PASS) : " + str(err))
        finally:
            return app.render_template(req, "reset_password.html", resp)
