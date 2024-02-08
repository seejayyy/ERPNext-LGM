# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _

class TechnologicalRequestSheetsLGM(Document):
	pass

# function to automatically create the stage for the request sheet 
@frappe.whitelist()
def create_stages_lgm(doc):
	# parse to json object
	doc = json.loads(doc)

	# check if work order that is linked to the current request sheet already exists
	if len(frappe.db.get_all('Stages LGM', fields="request_sheet_link", filters={"request_sheet_link": doc["name"]})) > 0:
		frappe.throw(_("Stages for current technological request sheet already exists."))
	else:
		request_sheet_name = doc["name"]
		stage_doc = frappe.get_doc(dict(
			doctype="Stages LGM",
			request_sheet_link = request_sheet_name
		)).insert()

		stage_doc.save()

	return stage_doc

# function to create work order for current request sheet
@frappe.whitelist()
def create_work_order_lgm(doc):
	# parse to json object
	doc = json.loads(doc)

	# check if work order that is linked to the current request sheet already exists
	if len(frappe.db.get_all('Work Order LGM', fields="request_sheet_link", filters={"request_sheet_link": doc["name"]})) > 0:
		frappe.throw(_("Work Order for current technological request sheet already exists."))
	else:
		# get ingredients
		ingredients_lists = get_ingredients(doc)

		# populate child table 
		table_list = []
		for ingredient in ingredients_lists:
			table_list.append(
				{
					"mixer_no": ingredient[0],
					"ingredient": ingredient[1],
					"ingredient_weight": ingredient[2],
				}
			)

		# insert record
		work_order_lgm = frappe.get_doc(dict(
			doctype='Work Order LGM',
			request_sheet_link=doc["name"],
			weighing_table_lgm=table_list,
		)).insert()

		work_order_lgm.save()

	return work_order_lgm

# function to get all the ingredients in all the stages related to the current request sheet
def get_ingredients(doc):
	# get ingredients from commpounding ingredients child table
	ingredient_list = []
	stages = []
	# get all stages 
	for i in range (1,6):
		if doc.get("stage_"+str(i), None) is not None:
			stages.append(doc.get("stage_"+str(i)))
	# for each stage
	for stage in stages:
		stage_object = frappe.get_doc("Stages LGM", stage)
		# get all recipes in each stage
		for i in range (1,16):
			batch_weight_lgm = stage_object.get("batch_weight_lgm_" + str (i))
			# get all ingredients in each row of each reipce
			for row in batch_weight_lgm:
				recipe_no = row.get("mixer_no")
				ingredient_name = row.get("ingredient")
				ingredient_weight = row.get("ingredient_weight")
				if "RS-" not in ingredient_name:
					ingredient_list.append((recipe_no, ingredient_name, ingredient_weight))
	return ingredient_list

# function to query the stages related to the current request sheet
@frappe.whitelist()
def query_stages(doc):
	doc = json.loads(doc)
	stages = []
	# sort the stages in correct order
	for i in range (0,5):
		if len(stages) == 0:
			first_stage = frappe.get_list("Stages LGM", filters={'request_sheet_link': doc["name"], 'is_first_stage': 1})
			if len(first_stage) > 0:
				stages.append(("stage_"+str(i+1),first_stage[0]["name"]))
		else:
			next_stage = frappe.get_list("Stages LGM", filters={'previous_stage_link': stages[i-1][1]})
			if len(next_stage) > 0:
				stages.append(("stage_"+str(i+1), next_stage[0]["name"]))
			else:
				break
	return stages
