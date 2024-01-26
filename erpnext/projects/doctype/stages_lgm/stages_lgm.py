# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _

class StagesLGM(Document):
	pass


@frappe.whitelist()
def calculate_total_weight(doc):
	doc = json.loads(doc)
	output = []
	# each stage
	if len(doc["formulation_parts"]) > 0 and len(doc["ingredient_table"]) > 0:
		if doc["mixer_internal_mixer"] == 1:
			calculated_total_mixer_table = []
			calculate_total_weight_table = []
			mb_items = []
			mixer_volume_used = int(doc["mixer_volume_used"])
			formulation_list = doc["formulation_parts"]
			ingredient_list = doc["ingredient_table"]

			if len(formulation_list) == len(ingredient_list):
				no_of_mixer = formulation_list[0]["select_mixer_no"]
				# each recipe, calculate the density mb and mb mult factor
				for i in range (1, int(no_of_mixer) + 1):
					density_denominator = 0
					total_formulation = 0
					density_mb = 0
					mb_mult_factor = 0
					for j in range (len(formulation_list)):
						ingredient_name = ingredient_list[j]["ingredient"]
						ingredient_density = float(ingredient_list[j]["ingredient_density"])
						formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
						density_denominator += (formulation_part/ingredient_density)
						total_formulation += formulation_part
					
					density_mb = round(total_formulation / density_denominator, 4)
					mb_mult_factor = round(mixer_volume_used / total_formulation * density_mb, 4)
					calculated_total_mixer_table.append(["formulation", total_formulation, "masterbatch_mult_factor", mb_mult_factor, "density_masterbatch", density_mb])
					mb_items.append(create_masterbatch_item(doc,density_mb, i))
				print(mb_items)
				# each recipe, calculate ingredient weight and the masterbatch weight of the recipe
				for i in range (1, int(no_of_mixer) + 1):
					mb_mult_factor = calculated_total_mixer_table[i-1][3]
					total_weight_mb = 0
					for j in range (len(formulation_list)):
						ingredient_name = ingredient_list[j]["ingredient"]
						formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
						ingredient_weight = mb_mult_factor * formulation_part
						total_weight_mb += ingredient_weight
						calculate_total_weight_table.append(["mixer_no", i, "ingredient_name", ingredient_name, "ingredient_weight",ingredient_weight])
					calculate_total_weight_table.append(["mixer_no",i, "ingredient_name", mb_items[i-1], "ingredient_weight",total_weight_mb])

				output.append(calculated_total_mixer_table)
				output.append(calculate_total_weight_table)
			
		# elif doc["mixer_two_roll_mill_" + str(i)] == "1":
		# 	calculated_total_mill_weight = []
		# 	formulation_list = doc["formulation_parts_" + str(i)]
		# 	if len(formulation_list) != ingredient_list:
		# 		return False
		# 	else:
		# 		for i in range (len(formulation_list)):
		# 			ingredient = ingredient_list[i]
		# 			formulation = formulation_list[i]
		# 		output.append((i, calculated_weight))

		# else:
		# 	continue
			
	return output

def create_masterbatch_item(doc, density_mb, index):
	rs_name = doc["name"]
	mb_name = rs_name + "-MB-" + str(index)
	mb_item = frappe.get_doc({
		"doctype": "Item",
		"item_name": mb_name,
		"item_code": mb_name,
		"item_density": density_mb,
		"item_group": "Produce",
		"stock_uom": "Gram",
		"is_stock_item": 0
	}).insert()
	return (mb_item.item_name)