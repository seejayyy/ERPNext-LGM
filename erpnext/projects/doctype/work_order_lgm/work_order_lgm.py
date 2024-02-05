# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _
from frappe.integrations.utils import make_post_request

class WorkOrderLGM(Document):
	pass

@frappe.whitelist()
def trigger_nodered(doc, cdt, cdn):
	doc = json.loads(doc)
	raw_url = frappe.get_doc("LGM Settings").lgm_url 
	raw_port = frappe.get_doc("LGM Settings").lgm_port
	url = raw_url + ":" + raw_port + "/listen"
	headers = {
		'Content-type': 'application/json',
	}
	data = json.dumps({
		"url": raw_url,
		"doc": doc,
		"cdt": cdt,
		"cdn": cdn
	})
	resp = make_post_request(url, headers=headers, data=data)
	return resp

@frappe.whitelist(allow_guest=True)
def get_data_from_nodered():
	data = json.loads(frappe.request.data)
	doc_name = data["doc"]["name"]
	cdt = data["cdt"]
	cdn = data["cdn"]
	weight = data["weight"]
	doc = frappe.get_doc("Work Order LGM", doc_name)
	ingredient_list = doc.weighing_table_lgm
	for ingredient in ingredient_list:
		if ingredient.name == cdn:
			ingredient.weighed = weight
			doc.save()
			doc.reload()
			return True
	return False

@frappe.whitelist()
def create_job_card_lgm(doc):
	# parse to json object
	doc = json.loads(doc)
	# check if work order that is linked to the current request sheet already exists
	if len(frappe.db.get_all('Job Card LGM', fields="work_order", filters={"work_order": doc["name"]})) > 0:
		frappe.throw(_("Job Card for current work order already exists."))
	else:
		# get ingredients
		stages_ingredient_list = get_ingredients_per_stage(doc)
		for stage_doc in stages_ingredient_list:
			stage = stage_doc[0]
			mixer_no = stage_doc[1]
			ingredient_list = stage_doc[2]
			mixing_instruction = frappe.get_doc("Stages LGM", stage).mixing_cycle

			job_card_lgm = frappe.get_doc(dict(
				doctype='Job Card LGM',
				work_order = doc["name"],
				request_sheet=doc["request_sheet_link"],
				for_quantity=1,
				mixer_no_job_card=mixer_no,
				ingredients=ingredient_list,
				mixing_cycle=mixing_instruction,
				stage=stage
			)).insert()
			job_card_lgm.save()
			# print(job_card_lgm.ingredients)

	return True

def get_ingredients_per_stage(doc):
	stages = query_stages(doc)
	output = []
	for stage in stages:
		stage_doc = frappe.get_doc("Stages LGM", stage[1])
		no_of_mixer = int(stage_doc.formulation_parts[0].select_mixer_no)	
		ingredient_list_per_stage = stage_doc.batch_weight_lgm
		index = 0 
		for i in range (1, no_of_mixer + 1):
			stage_recipe_ingredients = []
			for j in range(0 + index, len(ingredient_list_per_stage)):
				
				ingredient = ingredient_list_per_stage[j]
				if int(ingredient.mixer_no) == i:
					if "RS-" in ingredient.ingredient:
						if int(stage_doc.is_first_stage) != 1:
							stage_recipe_ingredients.append({
								"mixer_no": ingredient.mixer_no,
								"ingredient": ingredient.ingredient,
								"ingredient_weight": ingredient.ingredient_weight,
							})
					else:
						stage_recipe_ingredients.append({
								"mixer_no": ingredient.mixer_no,
								"ingredient": ingredient.ingredient,
								"ingredient_weight": ingredient.ingredient_weight,
							})
				else:
					index = j
					break
			output.append((stage[1], i, stage_recipe_ingredients))
	return output

@frappe.whitelist()
def create_work_order_lgm(doc):
	# parse to json object
	doc = json.loads(doc)

	request_sheet_doc = frappe.get_doc("Technological Request Sheets LGM", doc["request_sheet_link"])
	# get ingredients
	ingredients_lists = get_ingredients_from_request_sheet(request_sheet_doc)

	# populate child table 
	table_list = []
	for ingredient in ingredients_lists:
		for ingredient_details in ingredient:
			table_list.append(
				{
					"ingredient": ingredient_details[0],
					"ingredient_weight": ingredient_details[1],
					"mixer_no": ingredient_details[2]
				}
			)

	# insert record
	doc["weighing_table_lgm"] = table_list
	return doc

def get_ingredients_from_request_sheet(doc):
	# get ingredients from commpounding ingredients child table
	ingredient_list = []
	compounding_list_object = doc.compounding_ingredients
	for list_object in compounding_list_object:
		mixer_no = int(list_object.select_mixer_no)
		ingredient_name = list_object.ingredient
		if ingredient_name != "Masterbatch":
			ingredient = []
			for i in range (1, mixer_no+1):
				if getattr(list_object,"mixer_" + str(i)) is not None:
					ingredient_weight = getattr(list_object,"mixer_" + str(i))
					ingredient.append((ingredient_name, ingredient_weight, i))
			ingredient_list.append(ingredient)

	# get ingredients from curing ingredients child table
	curing_list_object = doc.curing_ingredients
	for list_object in curing_list_object:
		mixer_no = int(list_object.select_mixer_no)
		ingredient_name = list_object.ingredient
		if ingredient_name != "Masterbatch":
			ingredient = []
			for i in range (1, mixer_no+1):
				if getattr(list_object,"mixer_" + str(i)) is not None:
					ingredient_weight = getattr(list_object,"mixer_" + str(i))
					ingredient.append((ingredient_name, ingredient_weight, i))
			ingredient_list.append(ingredient)
	return ingredient_list

@frappe.whitelist()
def get_all_work_order():
	data = frappe.get_all("Work Order LGM", fields="request_sheet_link")
	output = []
	for forms in data:
		if forms.request_sheet_link not in output:
			output.append(forms.request_sheet_link)
	return output

def query_stages(doc):
	stages = []
	request_sheet = doc["request_sheet_link"]
	for i in range (0,5):
		if len(stages) == 0:
			first_stage = frappe.get_list("Stages LGM", filters={'request_sheet_link': request_sheet, 'is_first_stage': 1})
			stages.append(("stage_"+str(i+1),first_stage[0]["name"]))
		else:
			next_stage = frappe.get_list("Stages LGM", filters={'previous_stage_link': stages[i-1][1]})
			if len(next_stage) > 0:
				stages.append(("stage_"+str(i+1), next_stage[0]["name"]))
			else:
				break
	return stages