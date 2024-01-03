# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe import _
from frappe.utils import flt, time_diff_in_hours, get_datetime, time_diff, get_link_to_form
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class JobCardLGM(Document):
	def validate(self):
		self.validate_time_logs()
		self.set_status()

	def validate_time_logs(self):
		self.total_completed_qty = 0.0
		self.total_time_in_mins = 0.0

		if self.get('time_logs'):
			for d in self.get('time_logs'):
				if get_datetime(d.from_time) > get_datetime(d.to_time):
					frappe.throw(_("Row {0}: From time must be less than to time").format(d.idx))

				data = self.get_overlap_for(d)
				if data:
					frappe.throw(_("Row {0}: From Time and To Time of {1} is overlapping with {2}")
						.format(d.idx, self.name, data.name))

				if d.from_time and d.to_time:
					d.time_in_mins = time_diff_in_hours(d.to_time, d.from_time) * 60
					self.total_time_in_mins += d.time_in_mins

				if d.completed_qty:
					self.total_completed_qty += d.completed_qty

			self.total_completed_qty = flt(self.total_completed_qty, self.precision("total_completed_qty"))

	def get_overlap_for(self, args):
		existing = frappe.db.sql("""select jc.name as name from
			`tabJob Card Time Log` jctl, `tabJob Card` jc where jctl.parent = jc.name and
			(
				(%(from_time)s > jctl.from_time and %(from_time)s < jctl.to_time) or
				(%(to_time)s > jctl.from_time and %(to_time)s < jctl.to_time) or
				(%(from_time)s <= jctl.from_time and %(to_time)s >= jctl.to_time))
			and jctl.name!=%(name)s
			and jc.name!=%(parent)s
			and jc.docstatus < 2
			and jc.employee = %(employee)s """,
			{
				"from_time": args.from_time,
				"to_time": args.to_time,
				"name": args.name or "No Name",
				"parent": args.parent or "No Name",
				"employee": self.employee
			}, as_dict=True)

		return existing[0] if existing else None

	def get_required_items(self):
		if not self.get('work_order'):
			return

		doc = frappe.get_doc('Work Order LGM', self.get('work_order'))
		# if doc.transfer_material_against == 'Work Order' or doc.skip_transfer:
		# 	return

		for d in doc.weighing_table_lgm:
			# if not d.operation:
			# 	frappe.throw(_("Row {0} : Operation is required against the raw material item {1}")
			# 		.format(d.idx, d.item_code))

			if self.get('for_quantity') == d.mixer_no:
				self.append('ingredients', {
					'ingredient': d.ingredient,
					'required_weight': d.weighed,
					'mixer_no': d.mixer_no
				})


	def on_submit(self):
		self.validate_job_card()
		self.update_work_order()
		self.set_transferred_qty()

	def on_cancel(self):
		self.update_work_order()
		self.set_transferred_qty()

	def validate_job_card(self):
		if not self.time_logs:
			frappe.throw(_("Time logs are required for {0} {1}")
				.format(frappe.bold("Job Card"), get_link_to_form("Job Card", self.name)))

		if self.for_quantity and self.total_completed_qty != self.for_quantity:
			total_completed_qty = frappe.bold(_("Total Completed Qty"))
			qty_to_manufacture = frappe.bold(_("Qty to Manufacture"))

			frappe.throw(_("The {0} ({1}) must be equal to {2} ({3})"
				.format(total_completed_qty, frappe.bold(self.total_completed_qty), qty_to_manufacture,frappe.bold(self.for_quantity))))
			
	def set_status(self, update_status=False):
		if self.status == "On Hold": return

		self.status = {
			0: "Open",
			1: "Submitted",
			2: "Cancelled"
		}[self.docstatus or 0]

		if self.time_logs:
			self.status = 'Work In Progress'

		if (self.docstatus == 1 and
			(self.for_quantity == self.transferred_qty or not self.items)):
			self.status = 'Completed'

		# if self.status != 'Completed':
		# 	if self.for_quantity == self.transferred_qty:
		# 		self.status = 'Material Transferred'

		if update_status:
			self.db_set('status', self.status)

@frappe.whitelist()
def get_ingredients(doc):
	doc = json.loads(doc)
	if not doc['work_order']:
		return
	work_order_doc = frappe.get_doc('Work Order LGM', doc['work_order'])
	# print(doc)
	# if doc.transfer_material_against == 'Work Order' or doc.skip_transfer:
	# 	return
	if doc['for_quantity'] == 0:
		return
	ingredient_list = []
	for d in work_order_doc.weighing_table_lgm:
		# if not d.operation:
		# 	frappe.throw(_("Row {0} : Operation is required against the raw material item {1}")
		# 		.format(d.idx, d.item_code))
		if doc['for_quantity'] == int(d.mixer_no):
			ingredient_list.append({
				'ingredient': d.ingredient,
				'weight': d.weighed,
				'mixer_no': d.mixer_no
				})
	return ingredient_list