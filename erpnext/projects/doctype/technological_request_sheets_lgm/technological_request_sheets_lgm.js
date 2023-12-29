// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Technological Request Sheets LGM', {
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Work Order': 'Create Work Order'
		};
	},

	refresh: function(frm) {
		console.log(frm.doc.docstatus);
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Work Order LGM'), function() {
				frm.call({
					method:"create_work_order_lgm",
					args:{
						doc:frm.doc
					},
					callback:function(r){
						frappe.msgprint({
							message: __('Work Order LGM is created'),
							indicator: 'green'
						})
						return;
					},
				});
			}, __('Create'));

			
		}
	},

	before_save: function(frm){
		frm.call({
			method:"calculate_waste",
			args:{
				doc:frm.doc
			},
			callback:function(r){
				frm.set_value("mb_waste", r.message);
			},
		});
	},
});
