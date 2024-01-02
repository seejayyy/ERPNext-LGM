# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document

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

	# # check if work order that is linked to the current request sheet already exists
	# if len(frappe.db.get_all('Work Order LGM', fields="request_sheet_link", filters={"request_sheet_link": doc["name"]})) > 0:
	# 	frappe.throw(_("Work Order for current technological request sheet already exists."))
	# else:
	# 	# get ingredients
	# 	ingredients_lists = get_ingredients(doc)

	# 	# populate child table 
	# 	table_list = []
	# 	for ingredient in ingredients_lists:
	# 		for ingredient_details in ingredient:
	# 			table_list.append(
	# 				{
	# 					"ingredient": ingredient_details[0],
	# 					"ingredient_weight": ingredient_details[1],
	# 					"mixer_no": ingredient_details[2]
	# 				}
	# 			)

	# 	# insert record
	# 	work_order_lgm = frappe.get_doc(dict(
	# 		doctype='Work Order LGM',
	# 		request_sheet_link=doc["name"],
	# 		weighing_table_lgm=table_list,
	# 	)).insert()

	# 	work_order_lgm.save()

	# return work_order_lgm.name
	return "Done"