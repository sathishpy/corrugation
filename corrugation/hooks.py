# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "corrugation"
app_title = "Corrugation"
app_publisher = "sathishpy@gmail.com"
app_description = "Customizations for corrugation manufacturing Industry"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "sathishpy@gmail.com"
<<<<<<< HEAD
app_license = "GNUv3"
=======
app_license = "MIT"
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/corrugation/css/corrugation.css"
# app_include_js = "/assets/corrugation/js/corrugation.js"

# include js, css files in header of web template
# web_include_css = "/assets/corrugation/css/corrugation.css"
# web_include_js = "/assets/corrugation/js/corrugation.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "corrugation.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

before_install = "corrugation.install.before_install"
<<<<<<< HEAD
after_install = "corrugation.install.after_install"
=======
# after_install = "corrugation.install.after_install"
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "corrugation.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }
<<<<<<< HEAD
doc_events = {
    "Purchase Receipt": {
        "on_submit": "corrugation.corrugation.doctype.cm_paper_roll_register.cm_paper_roll_register.create_new_rolls",
    },
    "Purchase Invoice": {
        "on_submit": "corrugation.corrugation.doctype.cm_paper_roll_register.cm_paper_roll_register.update_invoice",
    },
    "Sales Invoice": {
        "on_update": "corrugation.corrugation.utils.set_sales_terms",
    },
    "*": {
        "on_update": "corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.add_doc_to_mirroring_queue",
        "on_submit": "corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.add_doc_to_mirroring_queue",
        "on_cancel": "corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.add_doc_to_mirroring_queue",
        "after_delete": "corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.add_doc_to_mirroring_queue",
    },
}
=======

>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a
# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"corrugation.tasks.all"
# 	],
# 	"daily": [
# 		"corrugation.tasks.daily"
# 	],
# 	"hourly": [
# 		"corrugation.tasks.hourly"
# 	],
# 	"weekly": [
# 		"corrugation.tasks.weekly"
# 	]
# 	"monthly": [
# 		"corrugation.tasks.monthly"
# 	]
# }
<<<<<<< HEAD
scheduler_events = {
#	"all": [
#		"corrugation.corrugation.doctype.cm_doc_mirror.cm_doc_mirror.mirror_doc_updates"
#	],
	"daily": [
		"corrugation.corrugation.utils.schedule_daily_jobs"
	]
}
=======
>>>>>>> 243d2cbcdd2be1575283550a2496da5aa3e6e60a

# Testing
# -------

# before_tests = "corrugation.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "corrugation.event.get_events"
# }
