# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe import _
from frappe.utils import flt, time_diff_in_hours, get_datetime, time_diff, get_link_to_form
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

# a job card to record the time logs for a manufacturing process.
class JobCardLGM(Document):
	def validate(self):
		self.validate_time_logs()
		self.set_status()

	# check the time log is a valid time or not.
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

	# function to call when the job card is submitted
	def on_submit(self):
		self.validate_job_card()

	# function to call to check the validity of the job card
	def validate_job_card(self):
		if not self.time_logs:
			frappe.throw(_("Time logs are required for {0} {1}")
				.format(frappe.bold("Job Card"), get_link_to_form("Job Card", self.name)))

		if self.for_quantity and self.total_completed_qty != self.for_quantity:
			total_completed_qty = frappe.bold(_("Total Completed Qty"))
			qty_to_manufacture = frappe.bold(_("Qty to Manufacture"))

			frappe.throw(_("The {0} ({1}) must be equal to {2} ({3})"
				.format(total_completed_qty, frappe.bold(self.total_completed_qty), qty_to_manufacture,frappe.bold(self.for_quantity))))
			
	# function to set the status of the job card
	def set_status(self, update_status=False):
		if self.status == "On Hold": return

		self.status = {
			0: "Open",
			1: "Submitted",
			2: "Cancelled"
		}[self.docstatus or 0]

		if self.time_logs:
			self.status = 'Work In Progress'

		if self.docstatus == 1:
			self.status = 'Completed'

		if update_status:
			self.db_set('status', self.status)

# a query function to get all the job cards that has the same work order
@frappe.whitelist()
def get_all_job_card():
	data = frappe.get_all("Job Card LGM", fields="work_order")
	output = []
	for forms in data:
		if forms.work_order not in output:
			output.append(forms.work_order)
	return output

# function to create stock entry
@frappe.whitelist()
def make_stock_entry(doc):
	doc = json.loads(doc)
	# get finished good and wip warehouse
	warehouses = frappe.get_all("Warehouse", fields="name")
	fg = None
	wip = None
	for warehouse in warehouses:
		if "Finished" in warehouse["name"]:
			fg = warehouse["name"]
		elif "Work In" in warehouse["name"]:
			wip = warehouse["name"]

	# calculate masterbatch weight by summing up all the ingredients weight in the table
	ingredient_list = doc["ingredients"]
	weight = 0
	for row in ingredient_list:
		weight += float(row["ingredient_weight"])
	weight = round(weight, 2)

	# query masterbatch item
	mb_item = frappe.get_list("Item", fields="name", filters={"name": doc["stage"] + "-MB-" + doc["mixer_no_job_card"]})[0]

	# put the masterbatch item in a dictionary 
	stock_entry_details = [dict(
		t_warehouse = fg,
		item_code = mb_item.name,
		qty = 1,
		allow_zero_valuation_rate = 1,
	)]

	# create stock entry
	stock_entry = frappe.get_doc(dict(
		doctype = "Stock Entry",
		stock_entry_type = "Manufacture",
		work_order_lgm = doc["work_order"],
		job_card_lgm = doc["name"],
		from_warehouse = wip,
		to_warehouse = fg,
		items = stock_entry_details,
	)).insert()
	stock_entry.save()
	stock_entry.submit()
	return True

# check if stock entry for this job card already exists
@frappe.whitelist()
def check_stock_entry(doc):
	doc = json.loads(doc)
	stock_entry = frappe.get_list("Stock Entry", fields="name", filters={"work_order_lgm": doc["work_order"], "job_card_lgm": doc["name"]})
	if len(stock_entry) > 0:
		return False
	return True