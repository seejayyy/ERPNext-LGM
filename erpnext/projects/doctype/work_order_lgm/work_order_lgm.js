// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Order LGM', {
	setup: function(frm){
		frm.call({
			method: "get_all_work_order",
			callback:function(r){
				var sheet_name = r.message;
				// prevent duplicate work order of the same request sheet
				frm.set_query("request_sheet_link", function(){
					return {
						filters: {
							"name": ["not in", sheet_name]
						}
					};
				})
			}
		});
	},

	before_save: function(frm){
		if (frm.doc["weighing_table_lgm"] == undefined){
			frm.call({
				method: "create_work_order_lgm",
				args:{
					doc:frm.doc
				},
				callback:function(r){
					return frm.doc = r.message;
				}
			});
		}
		
	},

	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Job Card LGM'), function() {
				frm.call({
					method:"create_job_card_lgm",
					args:{
						doc:frm.doc
					},
					callback:function(r){
						frappe.msgprint({
							message: __('Job Card is created'),
							indicator: 'green'
						})
					},
				});
			});
		}
	},

	before_submit(frm){
		var ingredients_list = frm.doc["weighing_table_lgm"];
		var no_of_ingredients = frm.doc["weighing_table_lgm"].length;
		for (var i = 0; i < no_of_ingredients; i++){
			console.log(ingredients_list[i]["weighed"])
			if (ingredients_list[i]["weighed"] == undefined){
				frm.reload_doc();
				frappe.throw({
					message: __(`Ingredient ${i+1} weight is not measured yet.`),
					indicator: 'red'
				});
			}
		}
	},
});


// child table 
frappe.ui.form.on('Ingredients Weighing Table LGM', {
    // cdt is Child DocType name i.e Quotation Item
    // cdn is the row name for e.g bbfcb8da6a
	get_weight(frm, cdt, cdn){
		frm.call({
			method:"trigger_nodered",
			callback:function(r){
				console.log(r.message);
				return;
			},
		});
	},
})
