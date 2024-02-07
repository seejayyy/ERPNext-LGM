// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Technological Request Sheets LGM', {
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Work Order': 'Create Work Order'
		};
	},

	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Stages LGM'), function() {
				frm.call({
					method:"create_stages_lgm",
					args:{
						doc:frm.doc
					},
					callback:function(r){
						frappe.set_route("Form", "Stages LGM", r.message.name);
					},
				});
			}).addClass("btn-primary");;

			// adds the button to create work order
			frm.add_custom_button(__('Create Work Order LGM'), function() {
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
						return frappe.set_route("Form", "Work Order LGM", r.message.name);;
					},
				});
			}).addClass("btn-primary");;
		}
	},

	onload: function(frm){
		if (frm.doc.docstatus === 1){
			frm.trigger('query_stages');
		}
	},
	
	query_stages: function(frm){
		frm.call({
			method: "query_stages",
			args:{
				doc:frm.doc
			},
			callback: function(r){
				if (r.message.length > 0){
					for (var i = 0; i < r.message.length; i++){
						frm.doc[r.message[i][0]] = r.message[i][1];
						frm.refresh_field(r.message[i][0]);
					}
				}
			}
		});
	},

});