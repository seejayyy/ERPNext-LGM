# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _

class StagesLGM(Document):
	pass

# function to calculate all the weights based on the inputs in compounding ingredient table and ingredient table
@frappe.whitelist()
def calculate_total_weight(doc):
	doc = json.loads(doc)
	output = []
	# each stage
	# if both tables have the same number of rows
	if (len(doc["formulation_parts"]) > 0 and len(doc["ingredient_table"]) > 0) and (len(doc["formulation_parts"]) == len(doc["ingredient_table"])):
		formulation_list = doc["formulation_parts"]
		ingredient_list = doc["ingredient_table"]
		mb_items = []
		calculate_total_weight_table = []
		# if internal mixer is selected
		if doc["mixer_internal_mixer"] == 1:
			calculated_total_mixer_table = []
			mixer_volume_used = int(doc["mixer_volume_used"])

			no_of_mixer = formulation_list[0]["select_mixer_no"]
			# each recipe, calculate the density masterbatch and masterbatch mult factor
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
				
				density_mb = round(total_formulation / density_denominator, 2)
				mb_mult_factor = round(mixer_volume_used / total_formulation * density_mb, 2)
				calculated_total_mixer_table.append(["formulation", total_formulation, "masterbatch_mult_factor", mb_mult_factor, "density_masterbatch", density_mb])
				mb_items.append(create_masterbatch_item(doc,density_mb, i))

			# print(mb_items)
			# each recipe, calculate ingredient weight and the masterbatch weight of the recipe
			for i in range (1, int(no_of_mixer) + 1):
				per_recipe_weight = []
				mb_mult_factor = calculated_total_mixer_table[i-1][3]
				total_weight_mb = 0
				for j in range (len(formulation_list)):
					ingredient_name = ingredient_list[j]["ingredient"]
					formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
					ingredient_weight = round(mb_mult_factor * formulation_part, 2)
					total_weight_mb += ingredient_weight
					per_recipe_weight.append(["mixer_no", i, "ingredient_name", ingredient_name, "ingredient_weight",ingredient_weight])
				# append masterbatch at the end of the recipe 
				per_recipe_weight.append(["mixer_no",i, "ingredient_name", mb_items[i-1], "ingredient_weight", round(total_weight_mb, 2)])
				calculate_total_weight_table.append(per_recipe_weight)

			output.append(calculated_total_mixer_table)
			output.append(calculate_total_weight_table)

		# if two roll mill is selected
		elif doc["mixer_two_roll_mill"] == 1:
			total_mill_weight = int(doc["mill_capacity"])
			mb_mill_weight = None
			if doc.get("mb_weight") is not None:
				mb_mill_weight = float(doc["mb_weight"])
			if mb_mill_weight is None:
				mb_mill_weight = total_mill_weight

			calculated_total_mill_table = []
			no_of_mixer = formulation_list[0]["select_mixer_no"]
			# each recipe, calculate the compounded mult factor masterbatch 
			for i in range (1, int(no_of_mixer) + 1):
				total_formulation = 0
				comp_mult_factor = 0
				for j in range (len(formulation_list)):
					ingredient_name = ingredient_list[j]["ingredient"]
					if "RS-" in ingredient_name:
						total_formulation = float(formulation_list[j]["formulation_mixer_"+str(i)])
						break
					else:
						formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
						total_formulation += formulation_part
				
				comp_mult_factor = round(mb_mill_weight / total_formulation, 2)
				calculated_total_mill_table.append(["formulation", total_formulation, "comp_mult_factor", comp_mult_factor])
				mb_items.append(create_masterbatch_item(doc, 0, i))

			# each recipe, calculate ingredient weight and the masterbatch weight of the recipe
			for i in range (1, int(no_of_mixer) + 1):
				per_recipe_weight = []
				comp_mult_factor = calculated_total_mill_table[i-1][3]
				total_weight_mill = 0
				for j in range (len(formulation_list)):
					ingredient_name = ingredient_list[j]["ingredient"]
					formulation_part = float(formulation_list[j]["formulation_mixer_"+str(i)])
					ingredient_weight = round(comp_mult_factor * formulation_part, 2)
					total_weight_mill += ingredient_weight
					per_recipe_weight.append(["mixer_no", i, "ingredient_name", ingredient_name, "ingredient_weight",ingredient_weight])
				# append masterbatch at the end of the recipe 
				per_recipe_weight.append(["mixer_no",i, "ingredient_name", mb_items[i-1], "ingredient_weight", round(total_weight_mill, 2)])
				calculate_total_weight_table.append(per_recipe_weight)
			output.append(calculated_total_mill_table)
			output.append(calculate_total_weight_table)
		return output
	else:
		return False

			
	
# function to create masterbatch item and insert into database
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
		"is_stock_item": 1
	}).insert()
	return (mb_item.item_name)

# function to auto remove the dummy items created 
@frappe.whitelist()
def remove_auto_created_item():
	items = frappe.get_list("Item", fields="name")
	autocreated_items = []
	for item in items:
		if "New Stages" in item.name:
			autocreated_items.append(item)
	for item in autocreated_items:
		frappe.delete_doc("Item", item.name)
	