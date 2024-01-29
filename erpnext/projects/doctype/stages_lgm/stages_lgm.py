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
	if (len(doc["formulation_parts"]) > 0 and len(doc["ingredient_table"]) > 0) and (len(doc["formulation_parts"]) == len(doc["ingredient_table"])):
		formulation_list = doc["formulation_parts"]
		ingredient_list = doc["ingredient_table"]
		mb_items = []
		calculate_total_weight_table = []
		if doc["mixer_internal_mixer"] == 1:
			calculated_total_mixer_table = []
			mixer_volume_used = int(doc["mixer_volume_used"])

			no_of_mixer = formulation_list[0]["select_mixer_no"]
			# each recipe, calculate the density mb and mb mult factor
			for i in range (1, int(no_of_mixer) + 1):
				density_denominator = 0
				total_formulation = 0
				density_mb = 0
				mb_mult_factor = 0
				for j in range (len(formulation_list)):
					ingredient_density = float(ingredient_list[j]["ingredient_density"])
					formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
					density_denominator += (formulation_part/ingredient_density)
					total_formulation += formulation_part
				
				density_mb = round(total_formulation / density_denominator, 4)
				mb_mult_factor = round(mixer_volume_used / total_formulation * density_mb, 4)
				calculated_total_mixer_table.append(["formulation", total_formulation, "masterbatch_mult_factor", mb_mult_factor, "density_masterbatch", density_mb])
				mb_items.append(create_masterbatch_item(doc,density_mb, i))

			# print(mb_items)
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

		elif doc["mixer_two_roll_mill"] == 1:
			total_mill_weight = int(doc["mill_capacity"])
			calculated_total_mill_table = []
			no_of_mixer = formulation_list[0]["select_mixer_no"]

			for i in range (1, int(no_of_mixer) + 1):
				total_formulation = 0
				comp_mult_factor = 0
				for j in range (len(formulation_list)):
					formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
					total_formulation += formulation_part
				
				comp_mult_factor = round(total_mill_weight / total_formulation, 4)
				calculated_total_mill_table.append(["formulation", total_formulation, "comp_mult_factor", comp_mult_factor])
				mb_items.append(create_masterbatch_item(doc, 0, i))

			# each recipe, calculate ingredient weight and the masterbatch weight of the recipe
			for i in range (1, int(no_of_mixer) + 1):
				comp_mult_factor = calculated_total_mill_table[i-1][3]
				total_weight_mill = 0
				for j in range (len(formulation_list)):
					ingredient_name = ingredient_list[j]["ingredient"]
					formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
					ingredient_weight = comp_mult_factor * formulation_part
					total_weight_mill += ingredient_weight
					calculate_total_weight_table.append(["mixer_no", i, "ingredient_name", ingredient_name, "ingredient_weight",ingredient_weight])
				calculate_total_weight_table.append(["mixer_no",i, "ingredient_name", mb_items[i-1], "ingredient_weight",total_weight_mill])
			output.append(calculated_total_mill_table)
			output.append(calculate_total_weight_table)
			print(output)
		return output
	else:
		return False

			
	

def create_masterbatch_item(doc, density_mb, index):
	rs_name = doc["name"]
	mb_name = rs_name + "-MB-" + str(index)

	prev_mb_items = frappe.get_list("Item",filters={"name": mb_name})
	if prev_mb_items is not None:
		for record in prev_mb_items:
			frappe.db.delete("Item", record)

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