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
		for k in range (1, 16):
			# per table
			ingredient_list_per_stage = stage_doc.get("batch_weight_lgm_" + str(k))
			if len(ingredient_list_per_stage) > 0:
				stage_recipe_ingredients = []
				for ingredient in ingredient_list_per_stage:
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
				output.append((stage[1], k, stage_recipe_ingredients))
	return output

@frappe.whitelist()
def create_work_order_lgm(doc):
	# parse to json object
	doc = json.loads(doc)

	# get ingredients
	ingredients_lists = get_ingredients_from_stages(doc)

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
	doc["weighing_table_lgm"] = table_list
	return doc

def get_ingredients_from_stages(doc):
	# get ingredients from commpounding ingredients child table
	ingredient_list = []
	stages = query_stages(doc)
	for stage in stages:
		stage_object = frappe.get_doc("Stages LGM", stage[1])
		for i in range (1,16):
			batch_weight_lgm = stage_object.get("batch_weight_lgm_" + str(i))
			for row in batch_weight_lgm:
				recipe_no = row.get("mixer_no")
				ingredient_name = row.get("ingredient")
				ingredient_weight = row.get("ingredient_weight")
				if "RS-" not in ingredient_name:
					ingredient_list.append((recipe_no, ingredient_name, ingredient_weight))
	return ingredient_list

@frappe.whitelist()
def check_stock_entry(doc):
	doc = json.loads(doc)
	ingredient_list = doc["weighing_table_lgm"]
	weights = {}
	for i in range (len(ingredient_list)):
		ingredient_name = ingredient_list[i]["ingredient"]
		ingredient_weight = float(ingredient_list[i]["weighed"])
		if weights.get(ingredient_name) is None:
			weights[ingredient_name] = ingredient_weight
		else:
			ori_weight = weights[ingredient_name]
			weights[ingredient_name] = ori_weight + ingredient_weight

	stock_entry_details = []
	warehouses = frappe.get_all("Warehouse", fields="name")
	stores = None
	wip = None
	for warehouse in warehouses:
		if "Stores" in warehouse["name"]:
			stores = warehouse["name"]
		elif "Work In" in warehouse["name"]:
			wip = warehouse["name"]

	for keys in weights.items():
		ingredient_name = keys[0]
		ingredient_weight = keys[1]
		stock_entry_detail = dict(
			s_warehosue = stores,
			t_warehouse = wip,
			item_code = ingredient_name,
			qty = ingredient_weight
		)
		stock_entry_details.append(stock_entry_detail)

	stock_entry = frappe.get_doc(dict(
		doctype = "Stock Entry",
		stock_entry_type = "Material Transfer",
		from_warehouse = stores,
		to_warehouse = wip,
		items = stock_entry_details
	)).insert()
	stock_entry.save()
	stock_entry.submit()
	return True
		
	# return output

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