// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Order LGM', {
	before_submit(frm){
		var ingredients_list = frm.doc["weighing_table_lgm"];
		var no_of_ingredients = frm.doc["weighing_table_lgm"].length;
		for (var i = 0; i < no_of_ingredients; i++){
			console.log(ingredients_list[i]["weighed"])
			if (ingredients_list[i]["weighed"] == undefined){
				frappe.throw({
					message: __(`Ingredient ${i+1} weight is not measured yet.`),
					indicator: 'red'
				})
			}
			frm.refresh();
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
						return;
					},
				});
			});
		}
	},

	before_save: function(frm){
		frm.call({
			method: "validate_request_sheet",
			args: {
				doc: frm.doc
			},
			callback:function(r){
				return frappe.throw(("Work Order for current request sheet already exists."));
			},
		});
	}
});


// child table 
frappe.ui.form.on('Ingredients Weighing Table LGM', {
    // cdt is Child DocType name i.e Quotation Item
    // cdn is the row name for e.g bbfcb8da6a
})
