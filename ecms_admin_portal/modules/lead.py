import frappe, logging


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
