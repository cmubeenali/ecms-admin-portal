import frappe, logging, json


class Lead:
    def fetch_lead_report(self, app, req, args):
        resp = {"data": []}
        try:
            query = """SELECT 
                t1.name AS lead_id,
                t1.lead_full_name, 
                DATE_FORMAT(t1.lead_lead_date,'%%b %%e, %%Y') as lead_date, 
                t1.lead_nationality, 
                t1.lead_phone_number, 
                t1.lead_status,
                COUNT(t2.name) AS follow_up_count,
                IFNULL(MAX(t2.session_remark_summary),'N/A') AS last_session_remark
            FROM 
                `tabLead` t1
            LEFT JOIN 
                `tabSession` t2 ON t1.name = t2.session_lead
            GROUP BY 
                t1.name, t1.lead_full_name, t1.lead_lead_source, t1.lead_nationality, t1.lead_phone_number, t1.lead_status
            ORDER BY 
                MAX(t2.modified) DESC, 
                t1.creation DESC;"""
            resp["data"] = frappe.db.sql(query=query, values=(), as_dict=True)
        except Exception as err:
            logging.error("API_ERROR(LEAD_RPT) : " + str(err))
            frappe.log_error("API_ERROR(LEAD_RPT) : " + str(err))
        finally:
            return app.json_response(json_data=resp)

    def fetch_sessions_by_lead(self, app, req, args):
        resp = {"status": "failed", "message": "Error occurred", "data": []}
        try:
            params = json.loads(req.data)
            resp["data"] = frappe.db.sql(
                """
            select t1.session_title as title, t1.session_type as type, DATE_FORMAT(t1.session_scheduled_for,'%%b %%e, %%Y') as scheduled_for, t1.session_status as status,
            IFNULL(t1.session_remark_summary,'N/A') as remark
            from `tabSession` t1
            where t1.session_lead=%s
            order by t1.creation desc; 
            """,
                values=(params["lead_id"]),
                as_dict=True,
            )
            resp["status"] = "success"
            resp["message"] = "Fetched sessions successfully"
        except Exception as err:
            logging.error("API_ERROR(LEADRPT_RFSBL) : " + str(err))
            frappe.log_error("API_ERROR(LEADRPT_RFSBL) : " + str(err))
        finally:
            return app.render_template(
                req, "lead_report_sessions.html", {"sessions": resp["data"]}
            )
