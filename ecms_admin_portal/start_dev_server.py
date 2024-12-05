if __name__ == '__main__':
    from werkzeug.serving import run_simple
    from ecms_applicant_portal.server import make_app
    app=make_app()
    run_simple('0.0.0.0', 4000, app, use_reloader=True,threaded=True)