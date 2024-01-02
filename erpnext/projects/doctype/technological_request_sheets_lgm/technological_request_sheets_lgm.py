# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _

class TechnologicalRequestSheetsLGM(Document):
	pass

"""Calculates the total waste of ingredients before production"""
@frappe.whitelist()
def calculate_waste(doc):
	doc = json.loads(doc)
		
	mb = doc["compounding_ingredients"][len(doc["compounding_ingredients"]) -1]
	curing = doc["curing_ingredients"][0]

	mb_mixer_count = int(mb["select_mixer_no"])
	mb_waste = 0

	for i in range(1, mb_mixer_count+1):
		waste_name = "mixer_" + str(i)
		mixer_name = "mixer_" + str(i)
		mb_waste += float(mb[waste_name]) - float(curing[mixer_name])

	mb_waste = round(mb_waste, 2)
	return mb_waste


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
			for ingredient_details in ingredient:
				table_list.append(
					{
						"ingredient": ingredient_details[0],
						"ingredient_weight": ingredient_details[1],
						"mixer_no": ingredient_details[2]
					}
				)

		# insert record
		work_order_lgm = frappe.get_doc(dict(
			doctype='Work Order LGM',
			request_sheet_link=doc["name"],
			weighing_table_lgm=table_list,
		)).insert()

		work_order_lgm.save()

	return work_order_lgm.name

def get_ingredients(doc):
	# get ingredients from commpounding ingredients child table
	ingredient_list = []
	compounding_list_object = doc["compounding_ingredients"]
	for list_object in compounding_list_object:
		mixer_no = int(list_object["select_mixer_no"])
		ingredient_name = list_object["ingredient"]
		if ingredient_name != "Masterbatch":
			ingredient = []
			for i in range (1, mixer_no+1):
				if "mixer_" + str(i) in list_object:
					ingredient_weight = list_object["mixer_" + str(i)]
					ingredient.append((ingredient_name, ingredient_weight, i))
			ingredient_list.append(ingredient)

	# get ingredients from curing ingredients child table
	curing_list_object = doc["curing_ingredients"]
	for list_object in curing_list_object:
		mixer_no = int(list_object["select_mixer_no"])
		ingredient_name = list_object["ingredient"]
		if ingredient_name != "Masterbatch":
			ingredient = []
			for i in range (1, mixer_no+1):
				if "mixer_" + str(i) in list_object:
					ingredient_weight = list_object["mixer_" + str(i)]
					ingredient.append((ingredient_name, ingredient_weight, i))
			ingredient_list.append(ingredient)
	print(ingredient_list)
	return ingredient_list