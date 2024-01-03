# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _

class WorkOrderLGM(Document):
	pass

@frappe.whitelist(allow_guest=True)
def get_weight_from_nodered():
	data = json.loads(frappe.request.data)
	order_no = data["work"]
	weight = data["weight"]
	mixer_no = data["mixer"]
	ingredient_name = data["name"]
	try:
		doc = frappe.get_doc("Work Order LGM", "Work-Order-" + str(order_no))
	except:
		frappe.throw("Work Order does not exist")
	ingredient_list = doc.weighing_table_lgm
	for ingredient in ingredient_list:
		if ingredient.ingredient == ingredient_name and ingredient.mixer_no == mixer_no:
			ingredient.weighed = weight
			doc.save()
			doc.reload()
			return "found"
	return "not found"


@frappe.whitelist()
def create_job_card_lgm(doc):
	# parse to json object
	doc = json.loads(doc)
	# check if work order that is linked to the current request sheet already exists
	if len(frappe.db.get_all('Job Card LGM', fields="work_order", filters={"work_order": doc["name"]})) > 0:
		frappe.throw(_("Job Card for current work order already exists."))
	else:
		# get ingredients
		ingredients_lists = get_ingredients(doc)

		# populate child table 
		for mixer in ingredients_lists:
			workstation_request_sheet = frappe.get_doc("Technological Request Sheets LGM", doc["request_sheet_link"]).factory_reference_no
			# insert record
			job_card_lgm = frappe.get_doc(dict(
				doctype='Job Card LGM',
				work_order = doc["name"],
				request_sheet=doc["request_sheet_link"],
				workstation = workstation_request_sheet,
				for_quantity=1,
				ingredients=mixer,
			)).insert()

			job_card_lgm.save()

	return True

def get_ingredients(doc):
	obj = doc["weighing_table_lgm"]
	no_of_mixer = 0
	initial_mixer = None
	for data in obj:
		if initial_mixer is None:
			initial_mixer = int(data["mixer_no"])
			no_of_mixer += 1
		else:
			if int(data["mixer_no"]) == initial_mixer:
				break
			else:
				no_of_mixer += 1

	output = [[] for _ in range (no_of_mixer)]
	for data in obj:
		output[int(data["mixer_no"])-1].append({
			"ingredient": data["ingredient"],
			"mixer_no": data["mixer_no"],
			"weight": data["weighed"],
		})
	return output


@frappe.whitelist()
def validate_request_sheet(doc):
	# parse to json object
	doc = json.loads(doc)
	# check if work order that is linked to the current request sheet already exists
	if len(frappe.db.get_all('Work Order LGM', fields="request_sheet_link", filters={"request_sheet_link": doc["request_sheet_link"]})) > 0:
		frappe.throw(_("Work Order for current request sheet already exists."))
		return False
	else:
		return True